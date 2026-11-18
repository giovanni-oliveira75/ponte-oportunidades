"""IFRN: editais com inscrições abertas na Área do Candidato."""
from __future__ import annotations

from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler import http
from crawler.classify import parse_br_date
from crawler.models import Opportunity

URL = "https://processoseletivo.ifrn.edu.br/"
NAME = "IFRN"


def parse(html: str) -> List[Opportunity]:
    soup = BeautifulSoup(html, "html.parser")
    items: List[Opportunity] = []
    for h2 in soup.find_all("h2"):
        if "inscri" not in h2.get_text().lower():
            continue
        box = h2.find_parent("div")
        for row in box.select("tbody tr"):
            link = row.select_one("h3 a")
            cells = row.find_all("td")
            if not link or len(cells) < 2:
                continue
            period = cells[1].get_text(" ", strip=True)
            end = period.split("até")[-1] if "até" in period else period
            deadline = parse_br_date(end)
            items.append(
                Opportunity(
                    title=link.get_text(" ", strip=True),
                    url=urljoin(URL, link["href"]),
                    source=NAME,
                    deadline=deadline.isoformat() if deadline else None,
                    summary=f"Inscrições: {period}",
                )
            )
    return items


def fetch() -> List[Opportunity]:
    return parse(http.get(URL).text)
