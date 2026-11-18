"""Links oficiais permanentes (calendários nacionais e cadastros), lidos de sources_fixed.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from crawler.models import Opportunity

FILE = Path(__file__).resolve().parents[2] / "sources_fixed.yaml"


def fetch() -> List[Opportunity]:
    data = yaml.safe_load(FILE.read_text(encoding="utf-8"))
    return [
        Opportunity(
            title=entry["title"],
            url=entry["url"],
            source=entry["source"],
            category=entry["category"],
            summary=entry.get("summary", ""),
            evergreen=True,
        )
        for entry in data
    ]
