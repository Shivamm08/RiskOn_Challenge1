"""
Builds the clean, refined main knowledge base from the real 339-page dump.
Filters out near-empty/unusable pages, auto-tags topics + region scope from
content (flagged as inferred, needs human review), outputs a clean HTML
directory matching the original structure.
"""
import os, re, json, sys
sys.path.insert(0, '/home/claude/database')
os.environ['XLSX_PATH'] = '/mnt/user-data/uploads/5_Summary_of_pages.xlsx'
from seed_database import ConfluenceTextExtractor, load_title_map

WIKI_DIR = "/home/claude/real_data/data- JB"
OUT_DIR = "/home/claude/clean_dataset/suitability_wiki"
os.makedirs(OUT_DIR, exist_ok=True)
title_map = load_title_map()

# Keyword vocabulary for auto-tagging (same vocabulary as the synthetic dataset,
# so it's compatible with existing SME topic_tags).
TOPIC_KEYWORDS = {
    "k_and_e": ["knowledge and experience", "k&e", "knowledge & experience"],
    "cip": ["client investment profile", "cip"],
    "client_classification": ["client classification", "professional client", "private client", "institutional client"],
    "cross_border": ["cross-border", "cross border", "domicile"],
    "finsa_scope": ["finsa", "fidleg"],
    "mifid_scope": ["mifid"],
    "cpr_alerts": ["consolidated product risk", "cpr", "pre-trade alert"],
    "concentration_risk": ["concentration risk", "issuer concentration"],
    "saa": ["strategic asset allocation", "saa"],
    "monitoring": ["overnight", "monitoring alert", "portfolio review"],
    "solicitation_type": ["solicitation", "actively solicited", "reverse solicited", "unsolicited"],
    "own": ["one way notification", " own "],
    "structured_products": ["structured product", "private equity", "third party fund"],
    "execution_only": ["execution-only", "execution only"],
    "kid_requirements": ["key information document", "kid", "priips"],
    "suitability_appropriateness": ["suitability", "appropriateness"],
}
REGION_KEYWORDS = {
    "CH": ["switzerland", "swiss", "fidleg"],
    "Monaco": ["monaco"],
    "Germany": ["germany", "german"],
    "EEA": ["eea", "europe", "european union"],
}

def auto_tag(text):
    t = text.lower()
    tags = [tag for tag, kws in TOPIC_KEYWORDS.items() if any(kw in t for kw in kws)]
    if not tags:
        tags = ["overview"]
    return tags

def auto_region(text):
    t = text.lower()
    hits = [r for r, kws in REGION_KEYWORDS.items() if any(kw in t for kw in kws)]
    if len(hits) == 1:
        return hits
    return ["CH", "Monaco", "Germany", "EEA"]  # default: broad, don't falsely narrow

kept, dropped = [], []

for fname in sorted(os.listdir(WIKI_DIR)):
    if not fname.endswith(".html"):
        continue
    page_id = fname[:-len(".html")]
    title, url = title_map.get(fname, (fname, None))
    with open(os.path.join(WIKI_DIR, fname), encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    ext = ConfluenceTextExtractor()
    ext.feed(raw)
    text = ext.text()

    if len(text) < 50:
        dropped.append({"id": page_id, "title": title, "reason": "near-empty (<50 chars extracted)"})
        continue

    tags = auto_tag(text)
    region = auto_region(text)

    out_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title></head>
<body>
<div class="page-metadata">Suitability Wiki &gt; {title}</div>
<h1>{title}</h1>
<div class="source-url">{url or ''}</div>
{raw}
</body></html>"""
    with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
        f.write(out_html)

    kept.append({
        "id": page_id, "title": title, "filename": fname, "topic_tags": tags,
        "region_scope": region, "source_url": url, "text_length": len(text),
    })

with open(os.path.join(OUT_DIR, "..", "page_index.json"), "w") as f:
    json.dump(kept, f, indent=2)
with open(os.path.join(OUT_DIR, "..", "dropped_pages.json"), "w") as f:
    json.dump(dropped, f, indent=2)

print(f"Kept: {len(kept)} pages -> {OUT_DIR}/")
print(f"Dropped: {len(dropped)} near-empty pages -> dropped_pages.json")
