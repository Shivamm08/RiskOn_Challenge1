# Database — Supabase / Postgres

## Why Supabase, not local SQLite

You're deploying to Vercel. Vercel's serverless functions get a fresh,
ephemeral filesystem on every invocation — a local SQLite file resets
constantly and is never actually shared between requests or users. Supabase
gives you a real, persistent, shared Postgres database with zero server
management and a generous free tier — the right tool for a live shared demo.

## Setup

1. Create a project at supabase.com (free tier is enough).
2. Project → SQL Editor → New query → paste all of `schema.sql` → Run.
   This has been verified with a real Postgres grammar parser (zero syntax
   errors) and every foreign key checked programmatically to reference a
   table that already exists at creation time.
3. Project → Settings → Database → copy the connection string (URI format).
4. Locally:
   ```bash
   pip install psycopg2-binary openpyxl --break-system-packages
   export DATABASE_URL="postgresql://postgres:[password]@[host]:5432/postgres"
   python3 seed_database.py
   ```

This seeds:
- **`wiki_pages`** — all 339 real Suitability Wiki pages, parsed from
  `real_wiki/*.html` using a Confluence-storage-format-aware parser (not a
  generic HTML stripper — this dataset uses `ac:`/`ri:` namespaced macro
  tags for info panels, images, and attachments, which a plain tag-stripper
  mangles). Titles and real Confluence URLs come from
  `5_Summary_of_pages.xlsx`, matched 339/339.
- **`experts`** — the 14-person global roster, 5-tier rank ladder.
- **`rms`** — the 3 demo RM profiles.

`topic_tags` and `region_scope` are left empty by the seed script — inferring
these from the real page content is real reasoning work (and is explicitly
part of what the challenge is scoring), not something to fake with a script.

## What's NOT seeded here (comes from the app, not this script)

`messages`, `kb_entries`, `kb_entry_reviews`, `notifications`, `audit_log` —
these fill up from real usage (the backend writing to them) once it's wired
to this database instead of local SQLite. That's the next step.

## Data quality note

50 of the 339 real pages extract under 200 characters of plain text (23 are
near-empty). Likely their real content lives in images/attachments rather
than prose. Worth a manual spot-check on the shortest ones before relying on
them for demo questions — check `wiki_pages` ordered by `length(plain_text)`
ascending once seeded.
