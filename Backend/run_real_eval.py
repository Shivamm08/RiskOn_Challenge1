import requests, json

import os
BASE = os.environ.get("BACKEND_URL", "http://localhost:8000")

# The real, official evaluation set + example questions, from JB's actual
# document (just uploaded), title-matched to the real 316-page dataset.
CASES = [
    # (question, expected_behavior, expected_title_contains)
    ("What triggers an Issuer Concentration Risk and how can I resolve it?", "clarify", None),
    ("What kind of explanation would be suitable to resolve a SAA alert?", "answer", "Strategic Asset Allocation"),
    ("How long do I have to fix an alert caused by Concentration Risk on a single position?", "clarify", None),
    ("I am blocked for entering a purchase order in Wealth Navigator, how can I unblock it?", "clarify", None),
    ("Is it mandatory for a Power of Attorney holder to have a K&E document?", "answer", "Knowledge"),
    ("How is the product risk of an instrument calculated?", "answer", "Methodology"),
    ("How can I change the K&E of an existing client?", "clarify", None),
    ("How can I enter a subscribe to 3rd party private Equity products?", "answer", None),
    ("The RM is located in Austria, the client in Japan, which client classification logic should be used?", "answer", "Classification"),
    ("Which alerts apply for the Advisory Location CH (BC CH) and an Advice Premium mandate?", "answer", None),
    ("Does DTM also apply for Trade Basic Service Model?", "answer", None),
    ("Which policy rules apply for Client Classification for Switzerland and which one for Monaco?", "answer", "Classification"),
    ("Can a PoA provide instruction for OWN?", "answer", None),
    ("Which session alerts are triggered for Advice Premium in Advisory Location CH?", "answer", None),
    ("I want to propose a Lombard loan, what do I need to check before advising the client?", "answer", None),
    ("I have actively recommended to buy a fund but receive a CPR alert, what shall I do?", "answer", None),
    ("What is a suitable recommendation?", "answer", None),
    ("What do I need to do to professionalize my client?", "answer", None),
    ("Why are Suitability and Appropriateness checks important?", "answer", None),
    ("Who is the local client classification responsible for Switzerland?", "answer", None),
    ("I need to document an account opening. Can you guide me through the process?", "answer", None),
    ("Who should fill the K&E if the client is a life insurance company?", "answer", None),
    ("Can a RM give advice on Digital assets to any client?", "answer", None),
    ("How can a RM verify client eligibility criteria for Digital Asset advice?", "answer", None),
    ("Which post-trade cost must be disclosed? What is the delivery mode in this case?", "answer", None),
    ("Can I record a phone call with a client domiciled in Germany? Is it mandatory to do so?", "answer", None),
    ("I forgot to send the Portfolio Analysis Report to my client. What are the consequences?", "answer", None),
    ("Help me preparing a PIR for my client", "answer", None),
]

results = []
for q, expected, title_hint in CASES:
    try:
        r = requests.post(f"{BASE}/ask", json={"question": q, "context": {}}, timeout=15)
        d = r.json()
        actual = {"answered": "answer", "clarification_needed": "clarify", "escalated": "escalate"}.get(d.get("status"), "?")
        ok = (actual == expected) or (expected == "answer" and actual == "escalate" and False)
        title_ok = True
        top_title = d["sources"][0]["page_title"] if d.get("sources") else None
        if title_hint and top_title:
            title_ok = title_hint.lower() in top_title.lower()
        results.append({"q": q, "expected": expected, "actual": actual, "ok": ok,
                         "top_title": top_title, "title_ok": title_ok,
                         "confidence": d.get("confidence", {}).get("answer_confidence")})
    except Exception as e:
        results.append({"q": q, "expected": expected, "actual": "ERROR", "ok": False, "error": str(e)})

correct = sum(1 for r in results if r["ok"])
print(f"\n=== {correct}/{len(results)} behavior-correct ===\n")
for r in results:
    flag = "OK  " if r["ok"] else "MISS"
    print(f"[{flag}] expected={r['expected']:8s} actual={r.get('actual','?'):8s} top='{r.get('top_title','-')}'  | {r['q'][:70]}")

with open("/tmp/real_eval_results.json", "w") as f:
    json.dump(results, f, indent=2)
