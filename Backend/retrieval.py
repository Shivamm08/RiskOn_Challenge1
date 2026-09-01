"""Ingestion & retrieval — loads the wiki HTML pages, strips markup, and
retrieves the best-matching page(s) for a question via TF-IDF cosine
similarity. Swap this module's internals for a real embedding model /
vector store later without touching main.py — retrieve() is the only
contract the rest of the app depends on.
"""
from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass
from html.parser import HTMLParser

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATASET_DIR = os.environ.get("DATASET_DIR", os.path.join(os.path.dirname(__file__), "..", "Dataset"))
WIKI_DIR = os.path.join(DATASET_DIR, "wiki")
PAGE_INDEX_PATH = os.path.join(DATASET_DIR, "page_index.json")


class _TextExtractor(HTMLParser):
    """Strips tags, keeps plain text. Table cells get a space separator so
    words from adjacent columns don't merge together."""

    def __init__(self):
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data):
        self.chunks.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.chunks)).strip()


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


@dataclass
class WikiPage:
    id: str
    title: str
    topic_tags: list[str]
    region_scope: list[str]
    filename: str
    text: str


class Retriever:
    def __init__(self):
        with open(PAGE_INDEX_PATH) as f:
            index = json.load(f)

        self.pages: list[WikiPage] = []
        for entry in index:
            path = os.path.join(WIKI_DIR, entry["filename"])
            with open(path, encoding="utf-8") as f:
                html = f.read()
            self.pages.append(
                WikiPage(
                    id=entry["id"],
                    title=entry["title"],
                    topic_tags=entry["topic_tags"],
                    region_scope=entry["region_scope"],
                    filename=entry["filename"],
                    text=_html_to_text(html),
                )
            )

        corpus = [f"{p.title} {p.text}" for p in self.pages]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, question: str, top_k: int = 3) -> list[tuple[WikiPage, float]]:
        """Returns up to top_k (page, similarity_score) pairs, highest first."""
        q_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(q_vec, self.matrix).flatten()
        ranked = sorted(range(len(self.pages)), key=lambda i: scores[i], reverse=True)
        return [(self.pages[i], float(scores[i])) for i in ranked[:top_k] if scores[i] > 0]

    def excerpt(self, page: WikiPage, question: str, max_len: int = 320) -> str:
        """Returns a short excerpt from the page's text most relevant to the
        question — the sentence with the highest keyword overlap, skipping
        sentences that are themselves phrased as a question (these are
        restated headings in the source pages, not answers)."""
        sentences = re.split(r"(?<=[.!?])\s+", page.text)
        q_words = {w.lower() for w in re.findall(r"\w+", question) if len(w) > 2}
        best, best_score = None, -1
        for s in sentences:
            if s.strip().endswith("?"):
                continue  # skip restated-question headings, we want the answer
            s_words = {w.lower() for w in re.findall(r"\w+", s)}
            score = len(q_words & s_words)
            if score > best_score:
                best, best_score = s, score
        if best is None:  # fallback: no non-question sentence found at all
            best = sentences[0] if sentences else page.text
        return best[:max_len].strip()


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
