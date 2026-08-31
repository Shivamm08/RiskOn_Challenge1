from __future__ import annotations
from dataclasses import dataclass
from .retrieval import RetrievedEvidence

@dataclass
class VerificationResult:
    decision:str; answer_confidence:float; answerable:bool; missing_information:list[str]; retrieval_relevance:float; groundedness:float; completeness_proxy:float; reason:str

def _missing_context(question:str)->list[str]:
    q=question.lower();m=[]
    if "concentration" in q and "alert" in q and all(x not in q for x in ["advisory session","client book","overnight"]): m.append("Was the alert triggered in an Advisory Session or in Client Book monitoring?")
    if ("change" in q or "update" in q) and "k&e" in q and "knowledge" not in q and "experience" not in q: m.append("Are you updating the Knowledge level or the Experience level?")
    if "blocked" in q and ("purchase order" in q or "wealth navigator" in q) and "because" not in q and "reason" not in q: m.append("What is the reason or alert causing the block?")
    return m

def verify(question:str,evidence:list[RetrievedEvidence],answer:str)->VerificationResult:
    missing=_missing_context(question)
    if missing: return VerificationResult("CLARIFY",0.20,False,missing,evidence[0].score if evidence else 0.0,0.0,0.0,"Required business context is missing.")
    top_score=evidence[0].score if evidence else 0.0;q=question.lower();top_jur=evidence[0].jurisdiction.lower() if evidence else ""
    scope_mismatch=("monaco" in q and top_jur=="ch") or ("europe" in q and top_jur=="ch")
    if scope_mismatch: return VerificationResult("ESCALATE",0.25,False,[],top_score,0.35,0.30,"The strongest retrieved source is outside the requested jurisdiction/scope.")
    retrieval_relevance=min(max(top_score*1.5,0.0),1.0);groundedness=0.95 if evidence and evidence[0].text.lower() in answer.lower() else 0.75;completeness_proxy=0.90 if len(answer)>80 else 0.65
    confidence=0.45*retrieval_relevance+0.35*groundedness+0.20*completeness_proxy
    if top_score<0.08: return VerificationResult("ESCALATE",confidence,False,[],retrieval_relevance,groundedness,completeness_proxy,"Available evidence is too weak to justify an answer.")
    return VerificationResult("ANSWER",confidence,True,[],retrieval_relevance,groundedness,completeness_proxy,"Evidence is sufficiently relevant for the MVP threshold.")
