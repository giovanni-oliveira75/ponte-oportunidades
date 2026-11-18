"""Comperve/UFRN: processos seletivos de cursos técnicos, com título oficial, último aviso e link de inscrição."""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler import http
from crawler.classify import extract_deadline, parse_br_date
from crawler.models import Opportunity

URL = "https://www.comperve.ufrn.br/"
NAME = "Comperve/UFRN"

_SCHOOLS = {
    "escolaagricola": ("Escola Agrícola de Jundiaí (UFRN)", "Macaíba"),
    "escolaenfermagem": ("Escola de Enfermagem (UFRN)", "Natal"),
    "escolamusica": ("Escola de Música (UFRN)", "Natal"),
    "imd": ("Instituto Metrópole Digital (UFRN)", "Natal"),
}
_MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
           "setembro", "outubro", "novembro", "dezembro"]

log = logging.getLogger(__name__)


def _school(path: str):
    for key, value in _SCHOOLS.items():
        if key in path:
            return value
    return ("UFRN", "")


def parse_home(html: str) -> List[Opportunity]:
    soup = BeautifulSoup(html, "html.parser")
    by_process: Dict[str, Opportunity] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/cursostecnicos/" not in href:
            continue
        base = urljoin(URL, re.sub(r"[^/]+\.php$", "", href))
        if base in by_process:
            continue
        school, city = _school(href)
        by_process[base] = Opportunity(
            title=f"Curso técnico: processo seletivo da {school}",
            url=base + "informacoes.php",
            source=NAME,
            apply_url=base + "inscricoes.php",
            apply_label="Inscrições",
            highlights=[city] if city else [],
            near=city in ("Natal", "Macaíba"),
        )
    return list(by_process.values())


def _news_date(text: str) -> Optional[str]:
    m = re.search(r"divulgada em (\d{1,2}) de (\w+) de (\d{4})", text.lower())
    if m and m.group(2) in _MONTHS:
        d = parse_br_date(f"{m.group(1)}/{_MONTHS.index(m.group(2)) + 1}/{m.group(3)}")
        return d.isoformat() if d else None
    return None


def short_title(official: str, school: str) -> str:
    """'PROCESSO SELETIVO 2026 PARA OS CURSOS TÉCNICOS ... SUBSEQUENTE ... INGRESSO ... 2027' -> título curto."""
    low = official.lower()
    if "subsequente" in low:
        kind = "Cursos técnicos subsequentes"
    elif "integrad" in low:
        kind = "Cursos técnicos integrados ao ensino médio"
    elif "técnic" in low or "tecnic" in low:
        kind = "Cursos técnicos"
    else:
        kind = "Processo seletivo"
    year = re.search(r"ingresso[^0-9]*(\d{4})", low)
    when = f" {year.group(1)}" if year else ""
    return f"{kind}{when}: {school}"


def enrich(opp: Opportunity, html: str) -> Opportunity:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    # Título oficial (ex.: "PROCESSO SELETIVO 2026 PARA OS CURSOS TÉCNICOS ... INGRESSO EM 2027")
    m = re.search(r"\n(PROCESSO SELETIVO[^\n]{10,200})\n", text)
    if m:
        opp.title = short_title(m.group(1), opp.title.split(" da ", 1)[-1])
    # Cada aviso vem como "texto do aviso" seguido de "(Divulgada em 17 de novembro de 2026)".
    lines = text.split("\n")
    news = []
    for i, line in enumerate(lines):
        if "(Divulgada em" in line:
            notice = re.sub(r"\s*\(Divulgada em[^)]*\)", "", line).strip() or (lines[i - 1] if i else "")
            news.append((notice, _news_date(line)))
    if news:
        notice, when = news[0]
        opp.published = when
        opp.summary = f"Último aviso: {notice}"
        news = [n for n, _ in news]
        deadline = extract_deadline(" ".join(news[:3]))
        if deadline:
            opp.deadline = deadline.isoformat()
    edital = soup.find("a", href=re.compile(r"edital\.php$"))
    if edital:
        opp.highlights.append("Edital disponível")
    return opp


# Se o último aviso é de fase posterior às inscrições, o processo não é mais oportunidade.
_CLOSED = re.compile(r"resultado|gabarito|aprovados|classifica|convoca|homologa", re.I)


def fetch() -> List[Opportunity]:
    items = []
    for opp in parse_home(http.get(URL).text):
        try:
            enrich(opp, http.get(opp.url).text)
        except Exception as exc:
            log.warning("Comperve: não consegui detalhar %s: %s", opp.url, exc)
        if not _CLOSED.search(opp.summary):
            items.append(opp)
    return items
