"""Draft reusable knowledge from an expert's resolution."""
from __future__ import annotations

import json
import os

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "question": {"type": "string"},
        "answer": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "question", "answer", "keywords"],
    "additionalProperties": False,
}


def draft_knowledge(question: str, expert_answer: str) -> dict:
    """Use the LLM when available; retain an editable safe draft on failure."""
    fallback = {
        "title": question[:100], "question": question, "answer": expert_answer,
        "keywords": [],
    }
    if not os.environ.get("OPENAI_API_KEY"):
        return fallback
    try:
        from openai import OpenAI
        response = OpenAI(timeout=10.0, max_retries=1).responses.create(
            model=os.environ.get("KNOWLEDGE_DRAFT_MODEL", os.environ.get("QUERY_REWRITE_MODEL", "gpt-4.1-mini")),
            instructions=(
                "Convert an expert-approved escalation answer into a concise reusable internal "
                "knowledge item. Preserve qualifications and jurisdiction. Do not add facts."
            ),
            input=f"Original question:\n{question}\n\nExpert answer:\n{expert_answer}",
            text={"format": {"type": "json_schema", "name": "knowledge_draft",
                             "schema": SCHEMA, "strict": True}},
            store=False,
        )
        return json.loads(response.output_text)
    except Exception:
        return fallback
