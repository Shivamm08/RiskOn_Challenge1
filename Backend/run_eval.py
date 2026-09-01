"""Runs Dataset/evaluation_set.json through the real /ask pipeline (in-process,
no server needed) and reports behavior accuracy + source accuracy — the
actual proof of calibration for the pitch, not just a number on the UI.

Usage: cd backend && python3 run_eval.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from models import AskRequest, QueryContext
import main as m

DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "Dataset")


def main():
    with open(os.path.join(DATASET_DIR, "evaluation_set.json")) as f:
        eval_set = json.load(f)
    with open(os.path.join(DATASET_DIR, "page_index.json")) as f:
        page_index = json.load(f)
    id_to_title = {p["id"]: p["title"] for p in page_index}

    correct_behavior = 0
    correct_source = 0
    n_answer_cases = 0
    rows = []

    for case in eval_set:
        req = AskRequest(question=case["question"], context=QueryContext())
        resp = m.ask(req)
        actual = {"answered": "answer", "clarification_needed": "clarify", "escalated": "escalate"}[resp.status]
        expected = case["expected_behavior"]
        behavior_ok = (actual == "answer" and expected in ("answer", "answer_with_scope_limit")) or (actual == expected)
        correct_behavior += behavior_ok

        source_ok = None
        if expected in ("answer", "answer_with_scope_limit") and case["expected_source_ids"]:
            n_answer_cases += 1
            expected_titles = {id_to_title[sid] for sid in case["expected_source_ids"]}
            actual_titles = {s.page_title for s in resp.sources}
            source_ok = bool(expected_titles & actual_titles)
            correct_source += bool(source_ok)

        rows.append({
            "id": case["id"], "question": case["question"], "expected": expected,
            "actual_status": resp.status, "confidence": resp.confidence.answer_confidence,
            "behavior_ok": behavior_ok, "source_ok": source_ok,
        })

    n = len(eval_set)
    print(f"\n=== Eval results: {n} real evaluation-set questions ===")
    print(f"Behavior accuracy: {correct_behavior}/{n} ({100*correct_behavior/n:.0f}%)")
    if n_answer_cases:
        print(f"Source accuracy (answer cases): {correct_source}/{n_answer_cases} ({100*correct_source/n_answer_cases:.0f}%)")
    print()
    for r in rows:
        flag = "OK  " if r["behavior_ok"] else "MISS"
        print(f"[{flag}] {r['id']:5s} expected={r['expected']:22s} actual={r['actual_status']:20s} conf={r['confidence']}")

    with open("eval_results.json", "w") as f:
        json.dump(rows, f, indent=2)
    print("\nFull results written to backend/eval_results.json")


if __name__ == "__main__":
    main()
