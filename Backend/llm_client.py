from __future__ import annotations

import json
import os
import re
from typing import Any, Iterable
from urllib import error, request

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


def _normalize_page(page: Any) -> dict[str, str]:
    title = getattr(page, "title", str(page))
    text = getattr(page, "text", "")
    return {"title": str(title), "text": str(text)}


def _fallback_answer(question: str, pages: Iterable[Any]) -> str:
    page_titles = [str(getattr(page, "title", page)) for page in pages[:2]]
    if page_titles:
        return (
            "I can only answer from the linked policy material, and the available sources do not clearly support a confident answer for this question. "
            f"Please clarify the scenario or check the relevant guidance in: {', '.join(page_titles)}."
        )
    return (
        "I cannot answer this confidently from the provided sources alone. "
        "Please clarify the client context, jurisdiction, or product details before I can provide a grounded answer."
    )


def is_insufficient_evidence(answer: str) -> bool:
    lowered = answer.lower()
    markers = (
        "not supported by the provided sources",
        "cannot answer this confidently",
        "i cannot answer this confidently",
        "please clarify",
        "insufficient evidence",
        "not enough information",
    )
    return any(marker in lowered for marker in markers)


def get_provider(model: str | None = None) -> str:
    configured = (os.getenv("AI_PROVIDER") or "").strip().lower()
    if configured:
        return configured
    if os.getenv("MOONSHOT_API_KEY"):
        return "moonshot"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "openai"


def get_model_name(provider: str | None = None, model: str | None = None) -> str:
    provider_name = (provider or get_provider()).lower()
    if model:
        return model
    if provider_name == "moonshot":
        return os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def build_context_prompt(question: str, pages: Iterable[Any], conversation_history: Iterable[dict[str, str]] | None = None) -> str:
    normalized = [_normalize_page(page) for page in pages]
    source_text = "\n\n".join(
        f"Source {idx + 1}: {page['title']}\n{page['text'].strip()}"
        for idx, page in enumerate(normalized)
    )

    history_text = ""
    if conversation_history:
        history_lines = []
        for turn in conversation_history:
            role = str(turn.get("role", "user")).strip()
            content = str(turn.get("content", "")).strip()
            if content:
                history_lines.append(f"{role.title()}: {content}")
        if history_lines:
            history_text = "Earlier chat context:\n" + "\n".join(history_lines) + "\n\n"

    return (
        "You are a suitability assistant. Answer only using the provided source material and the prior chat context where relevant. "
        "If the sources do not clearly answer the question, say that the answer is not supported by the provided sources and ask for clarification or escalate.\n\n"
        f"{history_text}"
        f"Question: {question}\n\n"
        f"Sources:\n{source_text}"
    )


def answer_with_context(question: str, pages: Iterable[Any], model: str | None = None, conversation_history: Iterable[dict[str, str]] | None = None) -> str:
    normalized_pages = list(pages)
    if not normalized_pages:
        return _fallback_answer(question, [])

    provider_name = (model or get_provider()).lower() if model else get_provider()
    api_key = None
    base_url = None

    if provider_name == "moonshot":
        api_key = os.getenv("MOONSHOT_API_KEY")
        base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        return _fallback_answer(question, normalized_pages)

    selected_model = get_model_name(provider_name, model)
    prompt = build_context_prompt(question, normalized_pages, conversation_history)
    payload = {
        "model": selected_model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "Answer only using the provided source material and the prior chat context where relevant. If the sources do not clearly answer the question, say so and request clarification or escalate.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if isinstance(content, list):
                flattened = "\n".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict)
                )
                if flattened:
                    return flattened.strip()
            if content:
                return str(content).strip()
    except (error.HTTPError, error.URLError, ValueError, KeyError, TypeError):
        pass

    return _fallback_answer(question, normalized_pages)
