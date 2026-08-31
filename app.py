from pathlib import Path
import streamlit as st
from src.pipeline import RiskONPipeline
BASE=Path(__file__).resolve().parent
pipeline=RiskONPipeline(BASE/'data')
st.set_page_config(page_title='RiskON MVP',layout='wide')
st.title('RiskON MVP — Know the Answer, Know the Limits, Know Who Knows')
st.caption('Synthetic-data prototype for Julius Baer RiskON Challenge')
question=st.text_area('RM question',value='Is K&E mandatory for a Power of Attorney holder who places orders?',height=90)
if st.button('Run assistant',type='primary'):
    result=pipeline.run(question);c1,c2=st.columns(2)
    with c1: st.metric('Decision',result['decision'])
    with c2: st.metric('Answer confidence',f"{result['answer_confidence']:.0%}")
    if result['decision']=='ANSWER': st.subheader('Verified answer');st.write(result['answer'])
    elif result['decision']=='CLARIFY':
        st.subheader('Clarification required')
        for item in result['clarification'] or []: st.info(item)
    else:
        st.subheader('Escalate to SME');r=result['routing'];st.write(f"**Recommended expert:** {r['expert_name']}");st.write(f"**Function:** {r['function']} ({r['lod']})");st.write(f"**Routing confidence:** {r['routing_confidence']:.0%}")
        for reason in r['reason']: st.write(f'- {reason}')
    st.subheader('Trust layer');v=result['verification'];st.write({'retrieval_relevance':round(v['retrieval_relevance'],3),'groundedness':round(v['groundedness'],3),'completeness_proxy':round(v['completeness_proxy'],3),'reason':v['reason']})
    st.subheader('Candidate evidence')
    for i,e in enumerate(result['evidence'],1):
        with st.expander(f"{i}. {e['title']} — score {e['score']:.3f}"):
            st.write(e['text']);st.caption(f"Jurisdiction: {e['jurisdiction']} | Topic: {e['topic']}")
