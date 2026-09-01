-- ============================================================================
-- Suitability Copilot — Database Schema (Supabase / Postgres)
-- ============================================================================
-- Run this in the Supabase SQL Editor (Project -> SQL Editor -> New query).
-- Tables are ordered so every foreign key references a table that already
-- exists by the time it's declared.
-- ============================================================================

drop schema if exists public cascade;
create schema public;

create extension if not exists "uuid-ossp";
create extension if not exists pg_trgm;   -- fast text search fallback alongside app-side TF-IDF

create type expert_rank as enum (
    'suitability_champion',
    'business_front_support',
    'expert',
    'senior_expert',
    'brm_suitability_lead'
);

-- ----------------------------------------------------------------------------
-- 1. SUITABILITY WIKI — the fixed, canonical knowledge source (no dependencies)
-- ----------------------------------------------------------------------------
create table wiki_pages (
    id              text primary key,           -- Confluence pageId, e.g. '732107229'
    title           text not null,
    raw_html        text not null,               -- original Confluence storage-format HTML
    plain_text      text not null,               -- stripped/parsed text used for retrieval
    topic_tags      text[] not null default '{}',
    region_scope    text[] not null default '{}', -- e.g. {'CH'}, {'CH','Monaco','Germany','EEA'}
    source_url      text,
    is_active       boolean not null default true,-- soft-disable a page without deleting it
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);
create index idx_wiki_pages_topic_tags on wiki_pages using gin (topic_tags);
create index idx_wiki_pages_text_trgm on wiki_pages using gin (plain_text gin_trgm_ops);

-- ----------------------------------------------------------------------------
-- 2. EXPERT ROSTER — 5-tier rank ladder, geography, live stats (self-ref only)
-- ----------------------------------------------------------------------------
create table experts (
    id                  uuid primary key default uuid_generate_v4(),
    name                text not null,
    office              text not null,
    region_tier         text not null,
    rank                expert_rank not null,
    utc_offset_minutes  integer not null,
    specialty           text,
    email               text unique,
    has_login           boolean not null default false,
    favorability_score  numeric(5,2) not null default 50.00,
    questions_answered  integer not null default 0,
    accuracy_pct        numeric(5,2) not null default 100.00,
    supervisor_id       uuid references experts(id),
    created_at          timestamptz not null default now()
);
create index idx_experts_office on experts (office);
create index idx_experts_rank on experts (rank);

-- ----------------------------------------------------------------------------
-- 3. RELATIONSHIP MANAGERS — RM profiles (no dependencies)
-- ----------------------------------------------------------------------------
create table rms (
    id                  uuid primary key default uuid_generate_v4(),
    name                text not null,
    office              text not null,
    years_at_jb         integer,
    client_segment      text,
    languages           text[] default '{}',
    specialization      text,
    email               text unique,
    created_at          timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- 4. ESCALATION THREADS — depends on experts, rms
-- ----------------------------------------------------------------------------
create table messages (
    id                  uuid primary key default uuid_generate_v4(),
    rm_id               uuid not null references rms(id),
    expert_id           uuid not null references experts(id),
    question            text not null,
    context             jsonb not null default '{}',
    routing_reasoning   text not null,
    routing_candidates  jsonb not null default '[]',
    status              text not null default 'pending'
                            check (status in ('pending', 'answered', 'added_to_kb', 'declined_kb')),
    created_at          timestamptz not null default now()
);

create table message_events (
    id              uuid primary key default uuid_generate_v4(),
    message_id      uuid not null references messages(id) on delete cascade,
    sender          text not null check (sender in ('rm', 'expert', 'system')),
    body            text not null,
    created_at      timestamptz not null default now()
);
create index idx_message_events_message_id on message_events (message_id);

-- ----------------------------------------------------------------------------
-- 5. CHAT-BASED KNOWLEDGE BASE — depends on experts, messages, wiki_pages
-- ----------------------------------------------------------------------------
create table kb_entries (
    id                  uuid primary key default uuid_generate_v4(),
    question            text not null,
    answer              text not null,
    contributed_by      uuid not null references experts(id),
    source_message_id   uuid references messages(id),
    status              text not null default 'published'
                            check (status in ('published', 'flagged', 'superseded', 'removed')),
    contradicts_wiki_page_id text references wiki_pages(id),
    endorsement_count   integer not null default 0,
    flag_count          integer not null default 0,
    trust_score         numeric(5,2) not null default 50.00,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);
create index idx_kb_entries_status on kb_entries (status);
create index idx_kb_entries_text_trgm on kb_entries using gin ((question || ' ' || answer) gin_trgm_ops);

create table kb_entry_reviews (
    id              uuid primary key default uuid_generate_v4(),
    kb_entry_id     uuid not null references kb_entries(id) on delete cascade,
    reviewer_id     uuid not null references experts(id),
    verdict         text not null check (verdict in ('endorse', 'flag')),
    note            text,
    created_at      timestamptz not null default now(),
    unique (kb_entry_id, reviewer_id)
);

-- ----------------------------------------------------------------------------
-- 6. NOTIFICATIONS — depends on kb_entries, messages
-- ----------------------------------------------------------------------------
create table notifications (
    id                  uuid primary key default uuid_generate_v4(),
    recipient_kind      text not null check (recipient_kind in ('rm', 'expert', 'all')),
    recipient_id        uuid,
    kind                text not null check (kind in ('kb_update', 'message')),
    title               text not null,
    body                text not null,
    related_kb_entry_id uuid references kb_entries(id),
    related_message_id  uuid references messages(id),
    read                boolean not null default false,
    created_at          timestamptz not null default now()
);
create index idx_notifications_recipient on notifications (recipient_kind, recipient_id, read);

-- ----------------------------------------------------------------------------
-- 7. AUDIT LOG — depends on rms, messages
-- ----------------------------------------------------------------------------
create table audit_log (
    request_id             uuid primary key default uuid_generate_v4(),
    rm_id                  uuid references rms(id),
    question                text not null,
    context                 jsonb not null default '{}',
    status                  text not null check (status in ('answered', 'clarification_needed', 'escalated')),
    answer                  text,
    answer_confidence       numeric(4,3),
    routing_confidence      numeric(4,3),
    sources                 jsonb not null default '[]',
    scope_flags             text[] not null default '{}',
    escalation_message_id   uuid references messages(id),
    reasoning_trail         text[] not null default '{}',
    resolved_by             text,
    final_answer            text,
    was_ai_correct          boolean,
    created_at              timestamptz not null default now(),
    resolved_at             timestamptz
);
create index idx_audit_log_created_at on audit_log (created_at desc);
create index idx_audit_log_status on audit_log (status);

-- ============================================================================
-- Trigger: keep kb_entries.trust_score and expert favorability in sync
-- ============================================================================
create or replace function apply_kb_entry_review() returns trigger as $$
begin
    if new.verdict = 'endorse' then
        update kb_entries
            set endorsement_count = endorsement_count + 1,
                trust_score = least(100, trust_score + 8),
                updated_at = now()
            where id = new.kb_entry_id;
        update experts e
            set favorability_score = least(100, e.favorability_score + 2)
            from kb_entries k
            where k.id = new.kb_entry_id and e.id = k.contributed_by;
    elsif new.verdict = 'flag' then
        update kb_entries
            set flag_count = flag_count + 1,
                status = 'flagged',
                updated_at = now()
            where id = new.kb_entry_id;
    end if;
    return new;
end;
$$ language plpgsql;

create trigger trg_kb_entry_review
    after insert on kb_entry_reviews
    for each row execute function apply_kb_entry_review();

-- ============================================================================
-- 8. MONITORING FLAGS — the second required deliverable: a system that
-- continuously checks AI responses for accuracy/completeness/currency
-- against the source, and proposes corrective action.
-- ============================================================================
create table monitoring_flags (
    id                  uuid primary key default uuid_generate_v4(),
    audit_request_id    uuid references audit_log(request_id),
    flag_type           text not null check (flag_type in ('groundedness', 'stale_source', 'contradicted')),
    detail              text not null,
    proposed_action     text not null,
    status              text not null default 'open' check (status in ('open', 'reviewed', 'resolved')),
    created_at          timestamptz not null default now()
);
create index idx_monitoring_flags_status on monitoring_flags (status);

-- ============================================================================
-- Table creation order used above (dependency-verified):
-- wiki_pages -> experts -> rms -> messages -> message_events -> kb_entries
-- -> kb_entry_reviews -> notifications -> audit_log -> monitoring_flags
--
-- Seed data (roster, RMs, real wiki pages) goes in via a separate Python
-- seed script — easier to keep in sync with Dataset/ than hand-written SQL.
-- ============================================================================
