# Backend v2 — Supabase-backed, real dataset, full decision flow

## What changed from v1

- **Database:** Postgres/Supabase instead of local SQLite (`db.py`) — the
  whole point was Vercel deployment needs persistent, shared state.
- **Retrieval:** now hybrid across TWO sources — the real 316-page wiki AND
  the chat-based knowledge base (`kb_entries`), both queried live from
  Postgres. Chat-KB entries are weighted by `trust_score`, so a flagged or
  low-trust contribution ranks lower even with a strong text match.
- **Real routing algorithm:** `escalation.py` now actually implements the
  geographic tier + rank + timezone-availability + track-record scoring
  that the frontend has been showing as reasoning — this used to be
  simulated, now it's real, queried against the live `experts` table.
- **Input normalization:** acronym expansion using JB's real glossary
  (K&E, CPR, FISR, DTM, etc.) before retrieval runs.
- **Self-verification:** every answer is checked against its own cited
  source before being shown as confident — if the groundedness check
  fails, the system escalates instead of showing a possibly-drifted answer.
- **Monitoring system (`monitoring.py`)** — this is JB's explicit **second
  deliverable**, not a bonus point: re-checks recent answers for
  groundedness and source staleness, writes findings to
  `monitoring_flags` with a proposed corrective action. Trigger with
  `POST /monitor/run`, review with `GET /monitor/flags`.
- **Real message threads:** escalating a question now creates an actual row
  in `messages`/`message_events`, not a mock object — this is what the
  Messages page and Expert Portal actually read.
- **Still no LLM anywhere in this path** — deliberate, per the reliability
  discussion. Purely extractive; the acronym expansion and self-verification
  above are the "hybrid" layer, not a generative model.

## Setup

```bash
cd backend
pip install -r requirements.txt --break-system-packages
export DATABASE_URL="postgresql://postgres:[password]@[host]:5432/postgres"
uvicorn main:app --reload
```

Prerequisite: `database/schema.sql` run in Supabase, then
`database/seed_database.py` run to populate `wiki_pages`, `experts`, `rms`.

## Endpoints

| Route | Purpose |
|---|---|
| `POST /ask` | Main decision flow — answer, clarify, or escalate |
| `POST /feedback` | Record an SME's resolution of an escalated question |
| `GET /audit` | Full audit trail |
| `GET /eval/summary` | Aggregate stats — the "evaluation dashboard" bonus point's data source |
| `POST /monitor/run` | Trigger the monitoring/QA pass (second deliverable) |
| `GET /monitor/flags` | Open monitoring flags needing human review |
| `POST /kb/reload` | Call after a new chat-KB entry is published so it's searchable immediately |

## Testing status — read this before assuming it just works

Every file passes a real syntax check and the FastAPI app builds cleanly
with all 8 routes registering correctly (verified in a sandbox with no live
Postgres available — network restrictions blocked installing one). This
is **not the same as integration-tested against a real database** the way
the SQLite version was end-to-end last time. Run one real request once
Supabase is connected and send me any error — fixing a real error is much
faster than me guessing blind.

## What's still open (per the requirements checklist from last turn)

- Evaluation dashboard is data-only (`/eval/summary`) — no UI yet, that's a
  frontend task.
- Automatic expert *discovery* from historical Q&A patterns isn't built —
  the roster is still manually seeded, just now scored dynamically rather
  than hardcoded per-question.
- `monitoring.py`'s contradiction check (wiki vs. chat-KB conflicting) is
  scaffolded in the schema (`kb_entries.contradicts_wiki_page_id`) but the
  actual conflict-detection logic isn't implemented yet — currently that
  field is only set manually when an expert flags it during submission.
