"""Ingestion & retrieval — loads the real wiki HTML pages, strips markup, and
retrieves the best-matching page(s) for a question via TF-IDF cosine
similarity. Swap this module's internals for a real embedding model /
vector store later without touching main.py — retrieve() is the only
contract the rest of the app depends on.
"""
from __future__ import annotations
import glob
import os
import re
from dataclasses import dataclass
from html.parser import HTMLParser

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WIKI_DIR = os.path.abspath(os.environ.get("WIKI_DIR", os.path.join(PROJECT_DIR, "pages")))

REGION_PATTERNS = {
    "CH": ("switzerland", "swiss", "booking centre ch", "bc ch"),
    "Monaco": ("monaco", "mc_local"),
    "Germany": ("germany", "german"),
    "EEA": ("eea", "european economic area", "european union"),
}


class _TextExtractor(HTMLParser):
    """Strips tags, keeps plain text. Table cells get a space separator so
    words from adjacent columns don't merge together."""

    def __init__(self):
        super().__init__()
        self.chunks: list[str] = []
        self.title_chunks: list[str] = []
        self._heading_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"h1", "title"} and not self.title_chunks:
            self._heading_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"h1", "title"} and self._heading_depth:
            self._heading_depth -= 1

    def handle_data(self, data):
        self.chunks.append(data)
        if self._heading_depth:
            self.title_chunks.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.chunks)).strip()

    def title(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.title_chunks)).strip()


def _parse_html(html: str) -> tuple[str, str]:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.title(), parser.text()


def _infer_regions(text: str) -> list[str]:
    lowered = text.lower()
    return [region for region, terms in REGION_PATTERNS.items() if any(term in lowered for term in terms)]


def _infer_topic_tags(title: str) -> list[str]:
    """Provide useful routing tags without relying on the synthetic index."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    return [word for word in words if len(word) > 2 and word not in ENGLISH_STOP_WORDS]


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
        self.pages: list[WikiPage] = []
        paths = sorted(glob.glob(os.path.join(WIKI_DIR, "*.html")))
        if not paths:
            raise RuntimeError(f"No HTML knowledge documents found in {WIKI_DIR}")

        for path in paths:
            filename = os.path.basename(path)
            page_id = os.path.splitext(filename)[0]
            with open(path, encoding="utf-8", errors="replace") as f:
                html = f.read()
            title, page_text = _parse_html(html)
            title = title or page_id
            self.pages.append(
                WikiPage(
                    id=page_id,
                    title=title,
                    topic_tags=_infer_topic_tags(title),
                    region_scope=_infer_regions(page_text),
                    filename=filename,
                    text=page_text,
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

    def term_coverage(self, page: WikiPage, question: str) -> float:
        """Share of meaningful query terms explicitly present in the source.

        This prevents generic TF-IDF overlap from being treated as evidence when
        the page omits the question's distinguishing concepts.
        """
        query_words = {
            word for word in re.findall(r"[a-z0-9]+", question.lower())
            if len(word) > 2 and word not in ENGLISH_STOP_WORDS
        }
        if not query_words:
            return 0.0
        page_words = set(re.findall(r"[a-z0-9]+", page.text.lower()))
        return len(query_words & page_words) / len(query_words)


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
