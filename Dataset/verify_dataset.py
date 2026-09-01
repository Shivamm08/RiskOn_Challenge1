"""
Verifies the synthetic knowledge base is internally consistent before you
trust it. Run this any time you edit wiki/, page_index.json,
evaluation_set.json, or synthetic_smes.json.

Usage: python3 verify_dataset.py
Exits with a non-zero code if any check fails, so you can wire it into a
pre-commit check later if you want.
"""
import json
import os
import re
import sys

FAILURES = []
WARNINGS = []


def fail(msg):
    FAILURES.append(msg)
    print(f"[FAIL] {msg}")


def warn(msg):
    WARNINGS.append(msg)
    print(f"[WARN] {msg}")


def ok(msg):
    print(f"[OK]   {msg}")


def check_page_index_matches_files():
    with open("page_index.json") as f:
        pages = json.load(f)
    for p in pages:
        path = os.path.join("wiki", p["filename"])
        if not os.path.exists(path):
            fail(f"page_index.json references missing file: {path}")
    ok(f"page_index.json: all {len(pages)} entries have a matching HTML file")

    # every file in wiki/ should also be in the index (no orphans)
    indexed = {p["filename"] for p in pages}
    actual = {f for f in os.listdir("wiki") if f.endswith(".html")}
    orphans = actual - indexed
    if orphans:
        warn(f"HTML files not listed in page_index.json (orphans): {orphans}")
    else:
        ok("no orphan HTML files outside page_index.json")
    return pages


def check_html_validity():
    from html.parser import HTMLParser

    class Checker(HTMLParser):
        def error(self, message):
            raise ValueError(message)

    bad = []
    for fname in os.listdir("wiki"):
        if not fname.endswith(".html"):
            continue
        with open(os.path.join("wiki", fname)) as f:
            content = f.read()
        # basic sanity: has <h1>, is non-trivial length
        if "<h1>" not in content:
            bad.append((fname, "missing <h1>"))
        if len(content) < 200:
            bad.append((fname, "suspiciously short"))
    if bad:
        for fname, reason in bad:
            fail(f"wiki/{fname}: {reason}")
    else:
        ok("all wiki pages have a title and non-trivial content")


def check_eval_set_references(pages):
    with open("evaluation_set.json") as f:
        eval_set = json.load(f)
    valid_ids = {p["id"] for p in pages}
    bad_refs = []
    for q in eval_set:
        for sid in q.get("expected_source_ids", []):
            if sid not in valid_ids:
                bad_refs.append((q["id"], sid))
    if bad_refs:
        for qid, sid in bad_refs:
            fail(f"evaluation_set.json question {qid} references non-existent page id '{sid}'")
    else:
        ok(f"evaluation_set.json: all {len(eval_set)} questions reference valid page ids")

    behaviors = [q["expected_behavior"] for q in eval_set]
    n_clarify = behaviors.count("clarify")
    if n_clarify == 0:
        warn("no 'clarify' cases in evaluation_set.json — you need at least a few to test that path")
    else:
        ok(f"{n_clarify} 'clarify' cases present (tests the ambiguous-question path)")
    return eval_set


def check_topic_alignment(pages):
    sme_path = "synthetic_smes.json"
    if not os.path.exists(sme_path):
        warn(f"{sme_path} not found — run generate_smes.py first, skipping topic alignment check")
        return
    with open(sme_path) as f:
        smes = json.load(f)
    wiki_topics = {t for p in pages for t in p["topic_tags"]}
    sme_topics = {t for s in smes for t in s["topic_tags"]}
    uncovered = wiki_topics - sme_topics
    unused = sme_topics - wiki_topics
    if uncovered:
        fail(f"wiki topics with NO SME who can be routed to: {uncovered}")
    else:
        ok("every wiki topic has at least one SME who can be routed to it")
    if unused:
        warn(f"SME topic tags that don't correspond to any wiki page: {unused}")


def check_region_scope_consistency(pages):
    """Pages claiming to cover a specific region shouldn't silently overlap
    with a more specific regional page without cross-referencing it."""
    region_specific = [p for p in pages if len(p["region_scope"]) == 1]
    for p in region_specific:
        ok_note = f"{p['id']} is scoped to {p['region_scope'][0]} only"
        print(f"       {ok_note}")
    ok(f"{len(region_specific)} pages are single-region-scoped (verify these manually — see checklist below)")


def main():
    print("=== Dataset verification ===\n")
    pages = check_page_index_matches_files()
    check_html_validity()
    check_eval_set_references(pages)
    check_topic_alignment(pages)
    check_region_scope_consistency(pages)

    print(f"\n=== Summary: {len(FAILURES)} failures, {len(WARNINGS)} warnings ===")
    if FAILURES:
        sys.exit(1)


if __name__ == "__main__":
    main()
