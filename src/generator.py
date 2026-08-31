from __future__ import annotations
from .retrieval import RetrievedEvidence

def generate_local_answer(question:str,evidence:list[RetrievedEvidence])->str:
    if not evidence: return "No supporting evidence was retrieved."
    top=evidence[0]
    return f"Based on the internal source '{top.title}': {top.text}"
