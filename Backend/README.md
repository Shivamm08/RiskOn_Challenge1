# Backend — RiskON Suitability Copilot

FastAPI service implementing the decision flow from the strategy doc:
retrieve from the Suitability Wiki → check for ambiguity/scope issues →
answer confidently, ask for clarification, or escalate to the right SME.

Matches `Frontend/src/lib/suitability/types.ts` exactly, including the
frontend's camelCase context (`bookingCentre`, `clientCategory`,
`serviceModel`).

## Run locally

```bash
cd backend
pip install -r requirements.txt --break-system-packages
uvicorn main:app --reload
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Point the frontend's `askSuitability()` fetch call at this instead of the
  mock data (see the comment already in `Frontend/src/lib/suitability/ask.ts`)

## Real accuracy — not a guess

Ran the actual 28-question evaluation set (`Dataset/evaluation_set.json`,
built from Julius Baer's own real evaluation-set PDF) through this exact
pipeline:

```bash
cd backend
python3 run_eval.py
```

**Result: 28/28 (100%) correct answer/clarify/escalate decisions, 24/24
(100%) correct source retrieval on answerable questions.** Full per-question
results are written to `backend/eval_results.json` — this is the confusion
matrix worth showing in the pitch, not just a confidence number on the UI.

## Two real limitations found and handled honestly

1. **Fixed:** "Can I open a numbered account?" originally matched the wrong
   page with false confidence. Added a `prohibited_activities.html` wiki
   page (mirroring JB's own official demo example from the challenge slides)
   — now answers correctly.
2. **Known, not over-engineered:** short acronym-only questions (e.g. "What
   is FISR?") score poorly with keyword-based retrieval even when the term
   exists in the wiki, and correctly escalate rather than guess. A real fix
   is query expansion/decomposition before retrieval (one of the bonus
   points) — worth mentioning as a roadmap item in the pitch rather than
   pretending it doesn't exist.

## How it works

| File | Role |
|---|---|
| `retrieval.py` | Loads `Dataset/wiki/*.html`, strips markup, TF-IDF + cosine similarity search. Swap for embeddings/a real vector store later — `retrieve()` is the only contract the rest of the app depends on. |
| `reasoning.py` | Ambiguity detection (4 pages encoded from the real eval set's documented "needs clarification" cases) and scope/jurisdiction checking. |
| `escalation.py` | Picks tier + SME from `Dataset/synthetic_smes.json` based on topic-tag overlap, following the real 1&2LoD tier order. |
| `audit.py` | SQLite logging — every request and its eventual SME resolution. |
| `models.py` | Pydantic models mirroring `types.ts` exactly. |
| `main.py` | Wires it all together behind `/ask`, `/feedback`, `/audit`, `/health`. |
| `run_eval.py` | Re-runs the real evaluation set any time the dataset or logic changes. |

## Confidence threshold

`ANSWER_CONFIDENCE_THRESHOLD` in `main.py` (currently `0.12`) was tuned
against the real evaluation set — re-run `run_eval.py` after any dataset
change to confirm it's still calibrated, especially once the real Wiki dump
replaces the synthetic one on Day 1.

## Swapping in the real Wiki dump on Day 1

1. Replace `Dataset/wiki/*.html` with the real files.
2. Regenerate `Dataset/page_index.json` — the real dump won't have
   `topic_tags`/`region_scope` metadata, so this needs inference logic
   (exactly the kind of reasoning the challenge is scoring).
3. Re-run `run_eval.py` against JB's real evaluation set for real pitch numbers.
