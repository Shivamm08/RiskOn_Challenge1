from pathlib import Path
import pandas as pd
from src.pipeline import RiskONPipeline
BASE=Path(__file__).resolve().parent;pipe=RiskONPipeline(BASE/'data');df=pd.read_csv(BASE/'data'/'evaluation.csv');rows=[]
for _,row in df.iterrows():
    r=pipe.run(row['question']);rows.append({'question':row['question'],'expected':row['expected_decision'],'predicted':r['decision'],'correct':r['decision']==row['expected_decision'],'answer_confidence':r['answer_confidence'],'top_evidence':r['evidence'][0]['title'] if r['evidence'] else ''})
out=pd.DataFrame(rows);print(out.to_string(index=False));print();print(f"Decision accuracy: {out['correct'].mean():.1%}")
for label in ['ANSWER','CLARIFY','ESCALATE']:
    part=out[out['expected']==label]
    if len(part): print(f"{label} accuracy: {part['correct'].mean():.1%} ({len(part)} cases)")
