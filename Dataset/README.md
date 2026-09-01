# Clean Dataset — Suitability Copilot

Two separate knowledge sources, matching the app's design:

```
suitability_wiki/     The FIXED main knowledge base (316 real pages)
chat_based_kb/         The GROWING knowledge base (starts empty, expert-contributed)
page_index.json         filename -> title -> topic_tags -> region_scope -> url
dropped_pages.json       23 pages excluded, with reasons
```

## suitability_wiki/ — how it was built

Started from the real 339-page Confluence export + the real
`5_Summary_of_pages.xlsx` title/URL mapping (339/339 matched, verified last
turn). From there:

1. **Filtered 23 near-empty pages** (under 50 characters of extractable
   text — likely image/attachment-only pages). Listed with reasons in
   `dropped_pages.json` — nothing was silently dropped.
2. **Auto-tagged the remaining 316** with `topic_tags` and `region_scope`,
   using keyword matching against the same vocabulary the synthetic dataset
   used (so it's compatible with the existing SME roster's topic tags with
   zero changes needed there).

**This tagging is a first pass, not verified ground truth** — it's inferred
from keyword presence, not read by a human. Distribution looks sane (every
topic has real coverage, only pages with a clearly dominant single region
got narrowed, everything else stayed broad/safe) but spot-check a sample
before fully trusting it, especially the region-scoped ones — a mis-scoped
page is exactly the kind of mistake the real evaluation set punishes.

## chat_based_kb/ — how it works

Starts empty. See its own README for format details — one HTML file per
published expert answer, generated from the `kb_entries` Postgres table,
not authoritative on its own (the database row is source of truth).

## Wiring this into the backend

Point `retrieval.py`'s `WIKI_DIR` at `suitability_wiki/` instead of the old
synthetic `Dataset/wiki/`, and point `PAGE_INDEX_PATH` at this folder's
`page_index.json`. The synthetic dataset (`Dataset/`) can now be deleted —
this is the real one. Retrieval should also read `chat_based_kb/` (or,
better, query `kb_entries` directly from Postgres) as a second corpus
alongside the wiki, exactly as designed — this wiring is the next step,
once the backend is updated to talk to Supabase instead of local SQLite.
