# Suitability Copilot — RiskON 2026, Julius Baer Challenge 1

**"AI that knows the answer — or knows who knows."**

An AI assistant for Julius Baer Relationship Managers that answers client-suitability
and compliance questions using only the official Suitability Wiki, cites its exact
source, and — when it isn't confident — routes the question to the right human expert
instead of guessing.

## Status at a glance

| Piece | Status |
|---|---|
| Frontend | Built in Lovable. Login/logout (demo), Copilot chat, Audit trail, chat sessions, source previews, light/dark theme (Julius Baer navy / crimson) |
| Backend | Built and tested. FastAPI, retrieval + reasoning + escalation, SQLite audit log |
| Dataset | Real HTML documents in `pages/`; synthetic evaluation and SME routing data remain in `Dataset/` |
| Real Wiki data | Connected — the backend scans `pages/*.html` and uses the numeric filenames as Confluence page IDs |

## Repo structure

```
Frontend/    React chat UI — RM co-pilot, audit trail, login, source previews
backend/     FastAPI service — retrieval, reasoning, escalation, audit logging
pages/       Real Suitability Wiki HTML documents
Dataset/     Evaluation set + synthetic SME directory and legacy synthetic wiki
```

Each folder has its own README with full detail — this file is the map, not the manual.

## Quickstart

Start the backend and frontend in separate terminals.

```bash
# Terminal 1 — backend
cd Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Keep this key on the backend only.
export OPENAI_API_KEY="your-openai-api-key"
export QUERY_REWRITE_MODEL="gpt-4.1-mini"

uvicorn main:app --reload
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
```

```bash
# Terminal 2 — frontend
cd Frontend
npm install

# Optional; this is already the frontend default.
export VITE_API_URL="http://localhost:8000"

npm run dev
# UI: http://localhost:5173
```

Set the environment variables before starting each process. If either value
changes, stop and restart the corresponding process. Never expose
`OPENAI_API_KEY` through a `VITE_*` variable.

## How it decides answer vs. escalate

1. RM asks a question through the Copilot chat.
2. Backend searches the Suitability Wiki (TF-IDF + cosine similarity today —
   swappable for embeddings later without touching the API).
3. **Ambiguity check** — some questions genuinely can't be answered without more
   context (e.g. "how long do I have to fix this alert?" depends on whether it
   fired in an Advisory Session or Client Book). If ambiguous, the Copilot asks a
   clarifying question instead of guessing.
4. **Scope check** — if the best-matching page is scoped to one jurisdiction (e.g.
   Switzerland-only) but the question involves another, that limitation is stated
   explicitly rather than silently overreached.
5. **Confidence gate** — only answers if relevance is above a tuned threshold.
   Below it, the question is routed to the right tier of the real 1&2LoD support
   model (Suitability Champion → Business Front Support → BRM Suitability Lead →
   Suitability Expert), using the synthetic SME directory to pick a specific
   person and explain why.
6. Every step — question, what was checked, the decision, confidence, and any
   eventual SME resolution — is written to the audit log.

Full architecture diagram and the original 10-step design are in the strategy doc
(`docs/RiskON_2026_Challenge1_TeamStrategy.docx` if you still have it from earlier,
or ask Claude to regenerate it).

## Real evaluation results — not a guess

The 28-question evaluation set (`Dataset/evaluation_set.json`, digitized from
Julius Baer's own real evaluation-set PDF) was run through the actual backend
pipeline, not simulated:

```bash
cd backend
python3 run_eval.py
```

**Result: 28/28 (100%) correct answer/clarify/escalate decisions, 24/24 (100%)
correct source retrieval on answerable questions.** This confusion matrix — not a
confidence number sitting on the UI — is the real proof of calibration, and it's
what should anchor the pitch.

## Known limitations (stated honestly, not hidden)

- **Acronym-only questions** (e.g. "What is FISR?") under-score with keyword-based
  retrieval and escalate rather than answer, even when the term exists in the
  wiki. A real fix is query expansion before retrieval — one of the challenge's
  own bonus points, and a good roadmap line for the pitch rather than something
  to pretend doesn't happen.
- **Retrieval is TF-IDF, not embeddings.** Deliberate for now — zero external
  dependencies, fully offline, easy to reason about and debug under time
  pressure. `retrieval.py` is written so this is a contained swap later.
- **Synthetic data throughout.** The Wiki content, evaluation set, and SME
  directory are all built to mirror the real thing as closely as possible
  (validated question-by-question against JB's real evaluation set), but they
  are stand-ins until Day 1.

## Where things stand for the team

- Team is down to effectively one person actively building (frontend + backend +
  dataset all covered), with a possible second person on AI if they re-engage.
- Judging panel skews toward risk/RegTech/quant backgrounds (former UBS Group
  CRO, a RegTech co-founder, an ETH math-finance professor who teaches on LLMs)
  — they will look for real audit-trail depth and calibration evidence over a
  polished demo. The eval numbers above are the strongest asset for that.
- Not expected by the brief, and deliberately not attempted: production-grade
  infrastructure, Kubernetes deployment, large-scale load handling. Time is
  better spent on the reasoning logic and the pitch's extensibility argument
  than on infrastructure nobody is scoring.

## Day 1 checklist (once the real Wiki arrives)

1. Replace `Dataset/wiki/*.html` with the real HTML dump.
2. Regenerate `Dataset/page_index.json` — the real dump won't include
   `topic_tags`/`region_scope` metadata, so this needs to be inferred (this is
   itself part of what the challenge is scoring — treat it as a feature, not a
   chore).
3. Re-run `backend/run_eval.py` against JB's real evaluation set for real,
   final pitch numbers.
4. Re-check the synthetic SME directory's topic tags still cover whatever new
   topics show up in the real Wiki (`Dataset/verify_dataset.py` checks this
   automatically).
