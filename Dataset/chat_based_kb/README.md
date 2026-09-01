# Chat-based Knowledge Base

This is the **second, separate knowledge source** — distinct from the fixed
Suitability Wiki. It starts empty and grows over time from real expert
answers, via the "Add this answer to the knowledge base?" flow in Messages.

## Format

One HTML file per published KB entry, matching the same structure as the
main wiki (so the same ingestion/retrieval pipeline can read both sources
without special-casing). Filename: `kb_<entry_id>.html`.

Each entry corresponds 1:1 to a row in the `kb_entries` Postgres table
(see database/schema.sql) — the HTML file is a human-readable export of
that row, not the source of truth. The database row is authoritative;
regenerate the HTML export from it if they ever drift.

## Example entry (see example_entry.html in this folder)

Structure: the original question, the expert's answer, who contributed it,
when, and its current trust/endorsement status — so it's inspectable the
same way a wiki page is, but visibly marked as expert-contributed rather
than official policy.

## Why HTML, not Word

Matches the main wiki's format exactly, so retrieval treats both sources
identically — no separate parser needed. A Word-doc export can be generated
from the same database rows later if that's genuinely still wanted (e.g.
for a compliance officer to review offline), but isn't the operational
format the app itself reads from.
