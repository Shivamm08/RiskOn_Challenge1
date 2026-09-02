"""Hybrid retrieval — extractive TF-IDF + cosine similarity over TWO
corpora: the fixed Suitability Wiki (wiki_pages) and the growing
chat-based knowledge base (kb_entries, published only). This is the
"Hybrid RAG backed by Extractive Sparse Retrieval" architecture: no LLM
in this path, purely retrieval + citation.

Reads from Postgres (Supabase) — the database is the source of truth, not
local files. Run database/seed_database.py first to populate wiki_pages.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import db


@dataclass
class RetrievedDoc:
    id: str
    title: str
    text: str
    topic_tags: list[str]
    region_scope: list[str]
    source_url: str | None
    source_type: Literal["wiki", "chat_kb"]
    trust_score: float = 100.0  # wiki pages are always fully trusted; chat KB varies
    extra: dict = field(default_factory=dict)  # e.g. {"answer": ...} for chat_kb


class Retriever:
    def __init__(self):
        self.docs: list[RetrievedDoc] = []
        self._load_wiki()
        self._load_chat_kb()
        if not self.docs:
            raise RuntimeError(
                "No documents loaded from the database. Did you run "
                "database/seed_database.py against your Supabase project?"
            )
        corpus = [f"{d.title} {d.title} {d.title} {d.title} {d.text}" for d in self.docs]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(corpus)

    def _load_wiki(self):
        rows = db.query(
            """SELECT id, title, plain_text, topic_tags, region_scope, source_url
               FROM wiki_pages WHERE is_active = true"""
        )
        for r in rows:
            self.docs.append(RetrievedDoc(
                id=r["id"], title=r["title"], text=r["plain_text"],
                topic_tags=r["topic_tags"] or [], region_scope=r["region_scope"] or [],
                source_url=r["source_url"], source_type="wiki", trust_score=100.0,
            ))

    def _load_chat_kb(self):
        rows = db.query(
            """SELECT id, question, answer, trust_score
               FROM kb_entries WHERE status = 'published'"""
        )
        for r in rows:
            self.docs.append(RetrievedDoc(
                id=str(r["id"]), title=r["question"], text=f"{r['question']} {r['answer']}",
                topic_tags=[], region_scope=[], source_url=None, source_type="chat_kb",
                trust_score=float(r["trust_score"]), extra={"answer": r["answer"]},
            ))

    def reload(self):
        """Call after a kb_entries change so new expert answers become searchable
        without restarting the process."""
        self.docs = []
        self._load_wiki()
        self._load_chat_kb()
        corpus = [f"{d.title} {d.title} {d.title} {d.title} {d.text}" for d in self.docs]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, question: str, top_k: int = 3) -> list[tuple[RetrievedDoc, float]]:
        """Returns (doc, score) pairs, highest first. Chat-KB entries are
        weighted by their trust_score (0-100) — a low-trust or flagged
        contribution ranks lower even with a strong text match, and a
        heavily-endorsed one gets a small boost. Wiki pages are always
        full-trust (100) since they're the fixed official source.

        A doc only counts as a real match if at least 2 distinct
        significant (4+ letter) words are shared with the question — a
        single coincidental shared word (e.g. "capital" matching both
        "capital of France" and "JB Natural Capital Score") isn't enough
        on its own, even with a title-boosted score. Caught by testing a
        deliberately nonsense question against the real system."""
        import re
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
        q_vec = self.vectorizer.transform([question])
        raw_scores = cosine_similarity(q_vec, self.matrix).flatten()
        q_words = {w.lower() for w in re.findall(r"\w+", question)
                   if len(w) >= 4 and w.lower() not in ENGLISH_STOP_WORDS}

        weighted = []
        for i, doc in enumerate(self.docs):
            doc_words = {w.lower() for w in re.findall(r"\w+", f"{doc.title} {doc.text}")
                         if len(w) >= 4 and w.lower() not in ENGLISH_STOP_WORDS}
            shared = len(q_words & doc_words)
            score = float(raw_scores[i]) * (0.5 + 0.5 * doc.trust_score / 100)
            if shared < 2:
                score = 0.0  # hard exclude — a single shared word (even title-boosted) isn't a real match
            weighted.append((doc, score))

        ranked = sorted(weighted, key=lambda x: x[1], reverse=True)
        return [(doc, score) for doc, score in ranked[:top_k] if score > 0]

    def excerpt(self, doc: RetrievedDoc, question: str, max_len: int = 320) -> str:
        """Best-matching, non-question-shaped sentence — same logic as before,
        now source-agnostic (works for both wiki text and chat_kb Q&A)."""
        import re
        text = doc.extra.get("answer", doc.text) if doc.source_type == "chat_kb" else doc.text
        sentences = re.split(r"(?<=[.!?])\s+", text)
        q_words = {w.lower() for w in re.findall(r"\w+", question) if len(w) > 2}
        best, best_score = None, -1
        for s in sentences:
            if s.strip().endswith("?"):
                continue
            s_words = {w.lower() for w in re.findall(r"\w+", s)}
            score = len(q_words & s_words)
            if score > best_score:
                best, best_score = s, score
        if best is None:
            best = sentences[0] if sentences else text
        return best[:max_len].strip()


_retriever: Retriever | None = None


def get_retriever(force_reload: bool = False) -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    elif force_reload:
        _retriever.reload()
    return _retriever
