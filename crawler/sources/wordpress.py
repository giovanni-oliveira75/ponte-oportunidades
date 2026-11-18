"""Fonte genérica para sites WordPress oficiais (API REST pública /wp-json/wp/v2).

Além do título, lê o conteúdo completo da matéria para extrair: resumo útil, prazo, vagas,
local e, principalmente, o link direto de inscrição citado no texto.
"""
from __future__ import annotations

import html as htmllib
import re
from datetime import date, timedelta
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from crawler import http
from crawler.classify import extract_deadline, highlights_from_text, is_near, is_relevant
from crawler.models import Opportunity

# Links dentro da matéria que costumam ser a inscrição de fato.
_APPLY_HINT = re.compile(
    r"inscri|inscreva|cadastr|formul|sympla|forms\.|docs\.google|forms\.gle|sigaa|edital"
    r"|candidat|seletiv|matricul|bit\.ly|even3|doity|gov\.br",
    re.I,
)
_SKIP_HOSTS = re.compile(r"instagram|facebook|twitter|x\.com|youtube|linkedin|whatsapp|tiktok|flickr", re.I)


def _clean(text: str) -> str:
    return htmllib.unescape(re.sub(r"<[^>]+>", " ", text or ""))


def find_apply_link(content_html: str, own_host: str) -> Optional[str]:
    soup = BeautifulSoup(content_html or "", "html.parser")
    best = None
    for a in soup.find_all("a", href=True):
        href, label = a["href"].strip(), a.get_text(" ", strip=True)
        host = urlparse(href).netloc
        if not href.startswith("http") or _SKIP_HOSTS.search(host):
            continue
        if host.endswith(own_host) and not _APPLY_HINT.search(href):
            continue  # link interno qualquer (outra notícia, home)
        if _APPLY_HINT.search(label) or _APPLY_HINT.search(href):
            return href
        best = best or href
    return best


def first_paragraphs(content_html: str, limit: int = 300) -> str:
    soup = BeautifulSoup(content_html or "", "html.parser")
    text = ""
    for p in soup.find_all("p"):
        chunk = p.get_text(" ", strip=True)
        if len(chunk) < 40:
            continue
        text = f"{text} {chunk}".strip()
        if len(text) >= limit:
            break
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "..."
    return text


class WordPressSource:
    def __init__(self, name: str, base_url: str, post_type: str = "posts",
                 searches: Optional[List[str]] = None, max_age_days: int = 21):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.host = urlparse(self.base_url).netloc.replace("www.", "")
        self.post_type = post_type
        self.searches = searches or [""]
        self.max_age_days = max_age_days

    def parse(self, posts: list, today: Optional[date] = None) -> List[Opportunity]:
        items = []
        for p in posts:
            title = _clean(p.get("title", {}).get("rendered", ""))
            content = p.get("content", {}).get("rendered", "")
            body = _clean(content)
            excerpt = _clean(p.get("excerpt", {}).get("rendered", ""))
            if not is_relevant(title, excerpt, require_signal=True):
                continue
            deadline = extract_deadline(f"{title} {body}", today)
            apply_url = find_apply_link(content, self.host)
            items.append(Opportunity(
                title=title,
                url=p["link"],
                source=self.name,
                published=(p.get("date") or "")[:10] or None,
                deadline=deadline.isoformat() if deadline else None,
                summary=first_paragraphs(content) or excerpt[:300],
                apply_url=apply_url,
                highlights=highlights_from_text(f"{title} {body}"),
                near=is_near(f"{title} {body}"),
            ))
        return items

    def fetch(self) -> List[Opportunity]:
        after = (date.today() - timedelta(days=self.max_age_days)).isoformat() + "T00:00:00"
        seen, items = set(), []
        for term in self.searches:
            url = (f"{self.base_url}/wp-json/wp/v2/{self.post_type}"
                   f"?per_page=30&after={after}&_fields=date,link,title,excerpt,content")
            if term:
                url += f"&search={term}"
            for opp in self.parse(http.get(url).json()):
                if opp.url not in seen:
                    seen.add(opp.url)
                    items.append(opp)
        return items
