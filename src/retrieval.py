from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class RetrievedEvidence:
    doc_id:str; title:str; text:str; score:float; jurisdiction:str=""; topic:str=""

class TfidfRetriever:
    def __init__(self,documents:list[dict[str,Any]])->None:
        self.documents=documents
        corpus=[f"{d.get('title','')} {d.get('topic','')} {d.get('text','')}" for d in documents]
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2),stop_words="english")
        self.matrix=self.vectorizer.fit_transform(corpus)
    def retrieve(self,question:str,top_k:int=4)->list[RetrievedEvidence]:
        q=self.vectorizer.transform([question]);scores=cosine_similarity(q,self.matrix)[0];idx=scores.argsort()[::-1][:top_k]
        out=[]
        for i in idx:
            d=self.documents[int(i)]
            out.append(RetrievedEvidence(d['id'],d['title'],d['text'],float(scores[i]),d.get('jurisdiction',''),d.get('topic','')))
        return out
