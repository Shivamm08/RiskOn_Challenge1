from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class RoutingResult:
    expert_name:str; function:str; lod:str; routing_confidence:float; reason:list[str]

class ExpertRouter:
    def __init__(self,experts_csv:str)->None:
        self.df=pd.read_csv(experts_csv)
        profiles=(self.df['function'].fillna('')+' '+self.df['lod'].fillna('')+' '+self.df['region'].fillna('')+' '+self.df['expertise'].fillna('')+' '+self.df['mandate'].fillna('')+' '+self.df['jurisdiction'].fillna('')).tolist()
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2),stop_words='english');self.matrix=self.vectorizer.fit_transform(profiles)
    def route(self,question:str)->RoutingResult:
        q=self.vectorizer.transform([question]);semantic=cosine_similarity(q,self.matrix)[0]
        quality=self.df['historical_success'].astype(float).to_numpy();latency=self.df['avg_response_minutes'].astype(float).to_numpy();latency_bonus=1-(latency-latency.min())/max(latency.max()-latency.min(),1)
        score=0.75*semantic+0.20*quality+0.05*latency_bonus;order=score.argsort()[::-1];i1=int(order[0]);i2=int(order[1]) if len(order)>1 else i1;row=self.df.iloc[i1];margin=max(float(score[i1]-score[i2]),0.0);confidence=min(0.55+0.45*margin+0.20*float(semantic[i1]),0.99)
        reasons=[f"Function/LoD match: {row['function']} ({row['lod']})",f"Expertise: {row['expertise']}",f"Mandate: {row['mandate']}",f"Jurisdiction/region: {row['jurisdiction']} / {row['region']}"]
        return RoutingResult(str(row['name']),str(row['function']),str(row['lod']),confidence,reasons)
