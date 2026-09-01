"""
Seeds the Supabase/Postgres database from:
  - the real Suitability Wiki (339 pages, Confluence storage-format HTML)
  - 5_Summary_of_pages.xlsx (filename -> title -> real Confluence URL)
  - the synthetic expert roster + RM profiles built earlier

Confluence storage format uses ac:/ri: namespaced tags for macros (info
panels, images, attachments) — a plain HTML tag-stripper mangles these.
This parser specifically unwraps the common macros into readable text
instead of dropping or garbling them.

Usage:
    export DATABASE_URL=postgresql://postgres.qobelhcafnawoaisanir:cAszo0-xehgaq-zysqyf@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
    pip install psycopg2-binary openpyxl --break-system-packages
    python3 seed_database.py
"""
import os
import re
import sys
import json
from html.parser import HTMLParser

import openpyxl
import psycopg2
from psycopg2.extras import execute_values

WIKI_DIR = os.environ.get("WIKI_DIR", "../Dataset/suitability_wiki")
PAGE_INDEX_PATH = os.environ.get("PAGE_INDEX_PATH", "../Dataset/page_index.json")
XLSX_PATH = os.environ.get("XLSX_PATH", "./5_Summary_of_pages.xlsx")
DATABASE_URL = os.environ.get("DATABASE_URL")


# ---------------------------------------------------------------------------
# Confluence storage-format -> plain text
# ---------------------------------------------------------------------------
class ConfluenceTextExtractor(HTMLParser):
    """Strips Confluence storage-format markup into readable plain text.
    Handles the common macros seen in this dataset: ac:structured-macro
    (info/warning panels, code blocks), ac:image + ri:attachment (embedded
    images -> a placeholder marker so we know an image was there), and
    ac:link + ri:page (internal cross-links -> kept as plain text)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self._in_macro_name = False
        self._current_macro = None

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag == "ac:structured-macro":
            self._current_macro = attrs_d.get("ac:name", "")
            if self._current_macro in ("info", "warning", "note", "tip"):
                self.chunks.append(f"\n[{self._current_macro.upper()}] ")
        elif tag == "ac:image":
            self.chunks.append(" [EMBEDDED IMAGE] ")
        elif tag in ("br",):
            self.chunks.append("\n")
        elif tag in ("tr",):
            self.chunks.append("\n")
        elif tag in ("td", "th", "li"):
            self.chunks.append(" ")

    def handle_data(self, data):
        self.chunks.append(data)

    def text(self) -> str:
        raw = "".join(self.chunks)
        return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", raw)).strip()


def load_title_map() -> dict[str, tuple[str, str]]:
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb.active
    mapping = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        filename, title, url = row[0], row[1], row[2]
        mapping[filename] = (title, url)
    return mapping


def load_wiki_pages():
    """Loads from the already-cleaned, already-tagged dataset (Dataset/) —
    the 23 near-empty pages are already filtered out, and topic_tags/
    region_scope are already auto-inferred. See Dataset/README.md for how
    that filtering/tagging was done."""
    with open(PAGE_INDEX_PATH) as f:
        index = json.load(f)
    pages = []
    for entry in index:
        html_path = os.path.join(WIKI_DIR, entry["filename"])
        with open(html_path, encoding="utf-8", errors="ignore") as f:
            raw_html = f.read()
        extractor = ConfluenceTextExtractor()
        extractor.feed(raw_html)
        pages.append({
            "id": entry["id"],
            "title": entry["title"],
            "raw_html": raw_html,
            "plain_text": extractor.text() or "(no extractable text)",
            "source_url": entry.get("source_url"),
            "topic_tags": entry.get("topic_tags", []),
            "region_scope": entry.get("region_scope", []),
        })
    return pages


# ---------------------------------------------------------------------------
# Expert roster + RM seed data (matches the roster designed earlier)
# ---------------------------------------------------------------------------
EXPERTS = [
    ("Nina Aebi", "Zurich", "Branch", "suitability_champion", 60, "General suitability triage", True),
    ("Daniel Frei", "Zurich", "Branch", "business_front_support", 60, "Operational execution issues", False),
    ("Elena Roth", "Geneva", "CH", "expert", 60, "Client classification", False),
    ("Marco Steiner", "Geneva", "CH", "senior_expert", 60, "Cross-border CH cases", True),
    ("Sophie Wyss", "Frankfurt", "EU", "senior_expert", 60, "MiFID add-on scope", False),
    ("Lukas Baumann", "Frankfurt", "EU", "brm_suitability_lead", 60, "Full MiFID Germany", False),
    ("Clara Suter", "London", "EU/UK", "senior_expert", 0, "UK-domiciled clients", False),
    ("Felix Graf", "Singapore", "APAC", "senior_expert", 480, "APAC structured products", False),
    ("Julia Marti", "Hong Kong", "APAC", "brm_suitability_lead", 480, "APAC regional escalations", False),
    ("Tobias Egli", "Tokyo", "Japan", "senior_expert", 540, "Japan-domiciled clients", False),
    ("Mia Widmer", "Tokyo", "Japan", "brm_suitability_lead", 540, "Japan regional escalations", False),
    ("Simon Kunz", "New York", "US", "senior_expert", -300, "US cross-border", False),
    ("Laura Moser", "New York", "US", "brm_suitability_lead", -300, "Americas regional escalations", False),
    ("Leon Zimmermann", "Dubai", "MEA", "senior_expert", 240, "MEA cross-border", False),
]

RMS = [
    ("A. Brunner", "Zurich", 6, "Private & Elected Professional, CH and Monaco", ["English", "German"], "Structured products, cross-border advisory"),
    ("L. Ferrari", "Monaco", 4, "Private clients, Monaco and France", ["English", "French", "Italian"], "Real estate-linked lending"),
    ("S. Keller", "Geneva", 9, "Institutional and Professional clients, CH", ["English", "German", "French"], "Portfolio management mandates"),
]


def main():
    if not DATABASE_URL:
        print("Set DATABASE_URL first, e.g.:")
        print('  export DATABASE_URL="postgresql://postgres:[password]@[host]:5432/postgres"')
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("Loading real, cleaned, tagged wiki pages...")
    pages = load_wiki_pages()
    execute_values(
        cur,
        """INSERT INTO wiki_pages (id, title, raw_html, plain_text, source_url, topic_tags, region_scope)
           VALUES %s ON CONFLICT (id) DO UPDATE SET
             title = excluded.title, raw_html = excluded.raw_html,
             plain_text = excluded.plain_text, source_url = excluded.source_url,
             topic_tags = excluded.topic_tags, region_scope = excluded.region_scope,
             updated_at = now()""",
        [(p["id"], p["title"], p["raw_html"], p["plain_text"], p["source_url"],
          p["topic_tags"], p["region_scope"]) for p in pages],
    )
    print(f"  Inserted/updated {len(pages)} wiki pages (with real topic_tags/region_scope).")

    print("Seeding expert roster...")
    for name, office, region_tier, rank, utc_off, specialty, has_login in EXPERTS:
        cur.execute(
            """INSERT INTO experts (name, office, region_tier, rank, utc_offset_minutes, specialty, has_login)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (name, office, region_tier, rank, utc_off, specialty, has_login),
        )
    print(f"  Inserted {len(EXPERTS)} experts.")

    print("Seeding RM profiles...")
    for name, office, years, segment, langs, spec in RMS:
        cur.execute(
            """INSERT INTO rms (name, office, years_at_jb, client_segment, languages, specialization)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (name, office, years, segment, langs, spec),
        )
    print(f"  Inserted {len(RMS)} RMs.")

    conn.commit()
    cur.close()
    conn.close()
    print("\nDone. wiki_pages, experts, and rms are seeded.")


if __name__ == "__main__":
    main()
