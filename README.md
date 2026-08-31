<<<<<<< HEAD
# RiskON MVP

Minimal runnable prototype for **AI that knows the answer — or knows who knows**.

## Core behavior
- **ANSWER** when evidence is sufficient.
- **CLARIFY** when required context is missing.
- **ESCALATE** when evidence is insufficient or out of scope.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Evaluation:
```bash
python evaluate.py
```

## Competition-day upgrade
Replace synthetic JSON with JB HTML + Excel metadata ingestion, then upgrade retrieval from TF-IDF to BM25(key words matching) + embeddings(semantic similarity) + metadata filters + reranker. Keep downstream interfaces unchanged.

## Confidence note
The MVP confidence score is a transparent heuristic, not a calibrated probability. A stronger version can fit logistic regression on real evaluation outcomes using retrieval relevance, faithfulness, completeness and answerability signals.
=======
# RiskOn_Challenge1
>>>>>>> fde338b86a8e6df599f48bf64a102b0e200453cc
