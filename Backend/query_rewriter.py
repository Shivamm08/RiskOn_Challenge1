"""Conversation-aware query rewriting for retrieval.

The feature is deliberately fail-open: retrieval continues with the user's
original question when the provider is disabled, unavailable, or malformed.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

from models import ChatMessage

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 6
MAX_MESSAGE_CHARS = 2_000

SYSTEM_PROMPT = """You are the strict scope gate and query rewriter for a wealth-management
RAG system. First decide whether the latest request has a meaningful, recognizable
connection to wealth-management suitability, compliance, client classification,
financial products, advisory/execution services, or related banking policy.

Set needs_retrieval to true ONLY when that connection is present in the latest
request or clearly established by the recent conversation. Set it to false for:
- nonsense, keyboard mashing, or random/meaningless strings;
- food, recipes, translation, entertainment, weather, and general knowledge;
- greetings, social chat, and any other unrelated request.

Examples: "Me gusta spaghetti" -> false; "idbfgisdf" -> false;
"Can I recommend this product to a Monaco client?" -> true;
"What is the deadline?" after discussing an issuer alert -> true.

When true, turn the latest request into a concise, self-contained search query
using only conversation facts. Resolve pronouns and omitted context. Preserve
exact identifiers, acronyms, dates, product names, and jurisdictions. Do not
answer or invent facts. Add useful exact search terms to keywords. When false,
copy the latest request into query and return an empty keywords list."""

REWRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "needs_retrieval": {"type": "boolean"},
    },
    "required": ["query", "keywords", "needs_retrieval"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class RewriteResult:
    query: str
    keywords: list[str] = field(default_factory=list)
    needs_retrieval: bool = True
    used_llm: bool = False
    fallback_reason: str | None = None


class QueryRewriter:
    def __init__(self, client=None):
        self.enabled = os.environ.get("QUERY_REWRITE_ENABLED", "true").lower() in {
            "1", "true", "yes", "on",
        }
        self.model = os.environ.get("QUERY_REWRITE_MODEL", "gpt-4.1-mini")
        self._client = client

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not os.environ.get("OPENAI_API_KEY"):
            return None
        from openai import OpenAI

        self._client = OpenAI(timeout=8.0, max_retries=1)
        return self._client

    def rewrite(self, question: str, history: list[ChatMessage]) -> RewriteResult:
        original = question.strip()
        if not self.enabled:
            return RewriteResult(original, fallback_reason="disabled")

        recent = history[-MAX_HISTORY_MESSAGES:]
        client = self._get_client()
        if client is None:
            return RewriteResult(original, fallback_reason="missing_api_key")

        transcript = "\n".join(
            f"{message.role}: {message.content[:MAX_MESSAGE_CHARS]}" for message in recent
        ) or "(no previous messages)"
        prompt = f"Recent conversation:\n{transcript}\n\nLatest user message:\n{original}"

        try:
            response = client.responses.create(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "retrieval_query",
                        "schema": REWRITE_SCHEMA,
                        "strict": True,
                    }
                },
                store=False,
            )
            payload = json.loads(response.output_text)
            rewritten = payload["query"].strip()
            if not rewritten:
                raise ValueError("rewriter returned an empty query")
            needs_retrieval = bool(payload["needs_retrieval"])
            keywords = (
                [str(item).strip() for item in payload["keywords"] if str(item).strip()]
                if needs_retrieval
                else []
            )
            return RewriteResult(
                query=rewritten,
                keywords=keywords,
                needs_retrieval=needs_retrieval,
                used_llm=True,
            )
        except Exception as exc:  # Retrieval must remain available if the LLM fails.
            logger.warning("Query rewrite failed; using original question: %s", exc)
            return RewriteResult(original, fallback_reason=type(exc).__name__)


_rewriter: QueryRewriter | None = None


def get_query_rewriter() -> QueryRewriter:
    global _rewriter
    if _rewriter is None:
        _rewriter = QueryRewriter()
    return _rewriter
