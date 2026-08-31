from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from .ingestion import load_documents
from .retrieval import TfidfRetriever
from .generator import generate_local_answer
from .verifier import verify
from .router import ExpertRouter

class RiskONPipeline:
    def __init__(self,data_dir:str|Path)->None:
        data_dir=Path(data_dir);docs=load_documents(data_dir/'documents.json');self.retriever=TfidfRetriever(docs);self.router=ExpertRouter(str(data_dir/'experts.csv'))
    def run(self,question:str)->dict:
        evidence=self.retriever.retrieve(question,top_k=4);answer=generate_local_answer(question,evidence);verification=verify(question,evidence,answer)
        result={'question':question,'decision':verification.decision,'answer_confidence':verification.answer_confidence,'verification':asdict(verification),'evidence':[asdict(e) for e in evidence],'answer':None,'clarification':None,'routing':None}
        if verification.decision=='ANSWER': result['answer']=answer
        elif verification.decision=='CLARIFY': result['clarification']=verification.missing_information
        else: result['routing']=asdict(self.router.route(question))
        return result
