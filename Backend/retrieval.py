"""Ingest and search the competition-day Confluence HTML export."""
from __future__ import annotations

import html as html_lib
import os
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_WIKI_DIR = Path(os.environ.get("WIKI_DIR", PROJECT_ROOT / "pages"))
WIKI_URL_BASE = os.environ.get("WIKI_URL_BASE", "http://localhost:8000/wiki/")
ALL_REGIONS = ["CH", "Monaco", "Germany", "EEA"]
REGION_PATTERNS = {
    "CH": re.compile(r"\b(?:switzerland|swiss|rml ch|bc ch|finsa|fidleg)\b", re.I),
    "Monaco": re.compile(r"\b(?:monaco|rml mc|mc_local)\b", re.I),
    "Germany": re.compile(r"\b(?:germany|german|bafin|full mifid)\b", re.I),
    "EEA": re.compile(r"\b(?:eea|mifid|european union|euro hub)\b", re.I),
}
TOPIC_PATTERNS = {
    "issuer_concentration": r"issuer concentration|concentration risk",
    "saa": r"\bsaa\b|strategic asset allocation",
    "k_and_e": r"knowledge (?:and|&) experience|\bk&e\b",
    "client_classification": r"client classification|professionalization|professionalise",
    "cpr": r"\bcpr\b|consolidated product risk|suitability check",
    "digital_assets": r"digital assets?|crypto",
    "private_equity": r"private equity|\bpe\b order",
    "phone_recording": r"voice recording|phone recording|record a call",
    "portfolio_analysis_report": r"portfolio analysis report|\bpir\b|suitability report",
    "cost_disclosure": r"cost disclosure|costs? (?:and|&) charges",
    "solicitation": r"solicitation|actively solicited|reverse solicited|unsolicited",
    "alerts": r"\balerts?\b|hard block|overnight monitoring",
    "account_opening": r"account opening",
    "product_risk": r"product risk|\bprr\b",
    "suitability": r"suitability|appropriateness",
}


def _clean(value: str) -> str:
    value = html_lib.unescape(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip(" |\t\r\n")


class _ConfluenceExtractor(HTMLParser):
    """Keep readable boundaries for Confluence tables, lists and headings."""
    BLOCKS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.headings: list[str] = []
        self._heading: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.BLOCKS:
            self.chunks.append("\n")
        elif tag in {"td", "th"}:
            self.chunks.append(" | ")
        elif tag == "br":
            self.chunks.append("\n")
        if tag in {"h1", "h2", "h3"}:
            self._heading = []
        title = dict(attrs).get("ri:content-title")
        if title:
            self.chunks.append(f" {title} ")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.BLOCKS or tag in {"td", "th"}:
            self.chunks.append("\n")
        if tag in {"h1", "h2", "h3"} and self._heading is not None:
            heading = _clean(" ".join(self._heading))
            if heading:
                self.headings.append(heading)
            self._heading = None

    def handle_data(self, data):
        self.chunks.append(data)
        if self._heading is not None:
            self._heading.append(data)

    def text(self) -> str:
        lines = [_clean(line) for line in "".join(self.chunks).splitlines()]
        return "\n".join(line for line in lines if line)


def _parse(raw: str) -> tuple[str, list[str]]:
    parser = _ConfluenceExtractor()
    parser.feed(raw)
    return parser.text(), parser.headings


def _linked_titles(raw: str) -> list[tuple[str, str]]:
    pairs = []
    pattern = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
    for href, body in pattern.findall(raw):
        match = re.search(r"(?:pageId=|/pages/)(\d+)", href)
        if not match:
            continue
        anchor, _ = _parse(body)
        title = _clean(anchor)
        if not title:
            title = _clean(unquote(urlparse(html_lib.unescape(href)).path).rsplit("/", 1)[-1].replace("+", " "))
        title = re.sub(r"\s+-\s+Suitability Wiki.*$", "", title, flags=re.I)
        if title and title.lower() not in {"here", "link", "see here"}:
            pairs.append((match.group(1), title))
    return pairs


def _fallback_title(page_id: str, text: str, headings: list[str]) -> str:
    generic = re.compile(r"^(contents?|topics? covered|related articles?)$", re.I)
    for value in headings + text.splitlines()[:8]:
        value = re.sub(r"^\d+[.)]?\s*", "", _clean(value))
        if 4 <= len(value) <= 140 and not generic.match(value):
            return value
    return f"Suitability Wiki page {page_id}"


def _topics(title: str, text: str) -> list[str]:
    haystack = f"{title}\n{text[:12000]}"
    tags = [tag for tag, pattern in TOPIC_PATTERNS.items() if re.search(pattern, haystack, re.I)]
    return tags or ["general_suitability"]


def _regions(title: str, text: str) -> list[str]:
    opening = f"{title}\n{text[:1500]}"
    found = [region for region, pattern in REGION_PATTERNS.items() if pattern.search(opening)]
    return found if len(found) == 1 else ALL_REGIONS.copy()


@dataclass
class WikiPage:
    id: str
    title: str
    topic_tags: list[str]
    region_scope: list[str]
    filename: str
    text: str

    @property
    def url(self) -> str:
        return f"{WIKI_URL_BASE}{self.id}"


class Retriever:
    def __init__(self, wiki_dir: str | os.PathLike | None = None):
        self.wiki_dir = Path(wiki_dir) if wiki_dir else REAL_WIKI_DIR
        files = sorted(self.wiki_dir.glob("*.html"))
        if not files:
            raise RuntimeError(f"No Wiki HTML found in {self.wiki_dir}; set WIKI_DIR to the pages folder")
        raw_by_id = {p.stem: p.read_text(encoding="utf-8", errors="replace") for p in files}
        inbound: dict[str, list[str]] = {}
        for raw in raw_by_id.values():
            for page_id, title in _linked_titles(raw):
                if page_id in raw_by_id:
                    inbound.setdefault(page_id, []).append(title)

        self.pages = []
        for page_id, raw in raw_by_id.items():
            text, headings = _parse(raw)
            candidates = inbound.get(page_id, [])
            title = max(set(candidates), key=lambda t: (candidates.count(t), len(t))) if candidates else _fallback_title(page_id, text, headings)
            self.pages.append(WikiPage(page_id, title, _topics(title, text), _regions(title, text), f"{page_id}.html", text))

        # Page titles are the strongest signal in this export. Repeat them to
        # counterbalance very long policy bodies and index/navigation pages.
        corpus = [f"{p.title}. {p.title}. {p.title}. {' '.join(p.topic_tags)}. {p.text}" for p in self.pages]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True, max_df=0.92)
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, question: str, top_k: int = 3) -> list[tuple[WikiPage, float]]:
        scores = cosine_similarity(self.vectorizer.transform([question]), self.matrix).flatten()
        return [(self.pages[i], float(scores[i])) for i in scores.argsort()[::-1][:top_k] if scores[i] > 0]

    def excerpt(self, page: WikiPage, question: str, max_len: int = 480) -> str:
        units = [u.strip() for u in re.split(r"\n+|(?<=[.!?])\s+", page.text) if u.strip()]
        q_words = {w.lower() for w in re.findall(r"[\w&]+", question) if len(w) > 2}
        best = max(units or [page.text], key=lambda u: (len(q_words & set(re.findall(r"[\w&]+", u.lower()))), min(len(u), max_len)))
        return best[:max_len].strip()


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
