"""IFRN: editais com inscrições abertas, enriquecidos com ofertas (campus, curso, vagas) e link de inscrição."""
from __future__ import annotations

import logging
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler import http
from crawler.classify import is_relevant, parse_br_date
from crawler.models import Opportunity

URL = "https://processoseletivo.ifrn.edu.br/"
NAME = "IFRN"
NEAR_CAMPUS = ("parnamirim", "natal", "são gonçalo", "sao goncalo")

log = logging.getLogger(__name__)


def parse_list(html: str) -> List[Opportunity]:
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
            items.append(Opportunity(
                title=link.get_text(" ", strip=True),
                url=urljoin(URL, link["href"]),
                source=NAME,
                deadline=deadline.isoformat() if deadline else None,
                summary=f"Inscrições de {period}.",
            ))
    return items


def enrich(opp: Opportunity, html: str) -> Opportunity:
    """Lê a página do edital: tabela de ofertas, taxa e links 'Realizar inscrição'."""
    soup = BeautifulSoup(html, "html.parser")
    offers = []
    for row in soup.select("table tbody tr"):
        cells = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        apply = row.find("a", string=lambda s: s and "inscri" in s.lower())
        if len(cells) >= 4 and apply:
            offers.append({"campus": cells[0], "curso": cells[1], "turno": cells[2],
                           "vagas": cells[3], "url": urljoin(URL, apply["href"])})

    text = soup.get_text(" ", strip=True).lower()
    if "taxa de inscrição" in text and "gratuita" in text:
        opp.highlights.append("Gratuito")

    if offers:
        near = [o for o in offers if o["campus"].lower().startswith(NEAR_CAMPUS)]
        best = (near or offers)[0]
        opp.apply_url = best["url"]
        opp.apply_label = f"Inscrever-se (campus {best['campus']})"
        opp.near = bool(near)
        total = sum(int(o["vagas"]) for o in offers if o["vagas"].isdigit())
        if total:
            opp.highlights.insert(0, f"{total} vagas")
        campi = sorted({o["campus"] for o in offers})
        shown = [c for c in campi if c.lower().startswith(NEAR_CAMPUS)] or campi[:3]
        opp.highlights.append(", ".join(shown) + (f" +{len(campi) - len(shown)} campi" if len(campi) > len(shown) else ""))
        cursos = sorted({o["curso"] for o in (near or offers)})
        opp.summary = (f"{opp.summary} Cursos: {'; '.join(cursos[:4])}"
                       + ("..." if len(cursos) > 4 else "."))
    return opp


def fetch() -> List[Opportunity]:
    items = [o for o in parse_list(http.get(URL).text) if is_relevant(o.title)]
    for opp in items:
        try:
            enrich(opp, http.get(opp.url).text)
        except Exception as exc:  # sem detalhes, o item continua com o link do edital
            log.warning("IFRN: não consegui detalhar %s: %s", opp.url, exc)
    return items
