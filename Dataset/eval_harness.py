"""
Eval harness — runs the pipeline against evaluation_set.json and reports
whether the answer/clarify/escalate decision matched the expected behavior,
and whether cited sources matched expected_source_ids.

This is currently a SKELETON: run_pipeline() is a stub. Wire it to the real
/ask endpoint (or call the pipeline function directly) once AI-1/AI-2's
logic exists. The scoring and reporting logic below is already complete and
does not need to change.

Usage:
    python3 eval_harness.py
"""
import json
import requests  # only needed if calling the live API; remove if calling in-process

API_URL = "http://localhost:8000/ask"


def run_pipeline(question: str) -> dict:
    """Replace this with a real call once the pipeline exists.
    Must return the AskResponse shape from docs/API_CONTRACT.md.
    """
    resp = requests.post(API_URL, json={"question": question, "context": {}})
    return resp.json()


def score():
    with open("evaluation_set.json") as f:
        eval_set = json.load(f)

    results = []
    correct_behavior = 0
    correct_sources = 0
    total_answer_cases = 0

    for case in eval_set:
        try:
            response = run_pipeline(case["question"])
        except Exception as e:
            results.append({"id": case["id"], "error": str(e)})
            continue

        # Map response status to our 3-way expected_behavior vocabulary.
        actual_status = response.get("status")
        actual_behavior = {
            "answered": "answer",
            "clarification_needed": "clarify",
            "escalated": "escalate",
        }.get(actual_status, "unknown")

        expected = case["expected_behavior"]
        # "answer_with_scope_limit" still counts as "answer" for behavior matching;
        # separately check scope_flags were populated.
        behavior_match = (
            actual_behavior == "answer" and expected in ("answer", "answer_with_scope_limit")
        ) or (actual_behavior == expected)

        if behavior_match:
            correct_behavior += 1

        source_match = None
        if expected in ("answer", "answer_with_scope_limit") and case["expected_source_ids"]:
            total_answer_cases += 1
            actual_titles = {s.get("page_title", "") for s in response.get("sources", [])}
            # loose match: at least one expected source id/title fragment appears
            source_match = any(
                sid.replace("_", " ") in " ".join(actual_titles).lower().replace("_", " ")
                or sid in " ".join(actual_titles).lower()
                for sid in case["expected_source_ids"]
            )
            if source_match:
                correct_sources += 1

        results.append({
            "id": case["id"],
            "question": case["question"],
            "expected_behavior": expected,
            "actual_status": actual_status,
            "behavior_match": behavior_match,
            "source_match": source_match,
            "confidence": response.get("confidence"),
        })

    n = len(eval_set)
    print(f"\n=== Eval Results: {n} questions ===")
    print(f"Behavior accuracy:  {correct_behavior}/{n} ({100*correct_behavior/n:.0f}%)")
    if total_answer_cases:
        print(f"Source accuracy (answer cases only): {correct_sources}/{total_answer_cases} ({100*correct_sources/total_answer_cases:.0f}%)")

    print("\n--- Per-question detail ---")
    for r in results:
        flag = "OK" if r.get("behavior_match") else "MISS"
        print(f"[{flag}] {r['id']}: expected={r.get('expected_behavior')} actual={r.get('actual_status')} conf={r.get('confidence')}")

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nFull results written to eval_results.json")


if __name__ == "__main__":
    score()
