from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def load_documents(path: str | Path) -> list[dict[str, Any]]:
    p=Path(path)
    with p.open("r",encoding="utf-8") as f: docs=json.load(f)
    required={"id","title","text"}
    for d in docs:
        m=required-set(d)
        if m: raise ValueError(f"Document missing fields {m}: {d}")
    return docs
