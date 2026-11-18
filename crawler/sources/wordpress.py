"""Fonte genérica para sites WordPress oficiais (API REST pública /wp-json/wp/v2)."""
from __future__ import annotations

import html as htmllib
import re
from datetime import date, timedelta
from typing import List, Optional

from crawler import http
from crawler.classify import extract_deadline, is_relevant
from crawler.models import Opportunity


def _clean(text: str) -> str:
    return htmllib.unescape(re.sub(r"<[^>]+>", " ", text or ""))


class WordPressSource:
    def __init__(self, name: str, base_url: str, post_type: str = "posts",
                 searches: Optional[List[str]] = None, max_age_days: int = 21):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.post_type = post_type
        self.searches = searches or [""]
        self.max_age_days = max_age_days

    def parse(self, posts: list, today: Optional[date] = None) -> List[Opportunity]:
        items = []
        for p in posts:
            title = _clean(p.get("title", {}).get("rendered", ""))
            summary = _clean(p.get("excerpt", {}).get("rendered", ""))[:280]
            if not is_relevant(title, summary, require_signal=True):
                continue
            deadline = extract_deadline(f"{title} {summary}", today)
            items.append(Opportunity(
                title=title,
                url=p["link"],
                source=self.name,
                published=(p.get("date") or "")[:10] or None,
                deadline=deadline.isoformat() if deadline else None,
                summary=summary,
            ))
        return items

    def fetch(self) -> List[Opportunity]:
        after = (date.today() - timedelta(days=self.max_age_days)).isoformat() + "T00:00:00"
        seen, items = set(), []
        for term in self.searches:
            url = (f"{self.base_url}/wp-json/wp/v2/{self.post_type}"
                   f"?per_page=50&after={after}&_fields=date,link,title,excerpt")
            if term:
                url += f"&search={term}"
            for opp in self.parse(http.get(url).json()):
                if opp.url not in seen:
                    seen.add(opp.url)
                    items.append(opp)
        return items
