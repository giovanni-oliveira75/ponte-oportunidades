"""Comperve/UFRN: avisos de processos seletivos de cursos técnicos (Escola Agrícola, Enfermagem...)."""
from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler import http
from crawler.models import Opportunity

URL = "https://www.comperve.ufrn.br/"
NAME = "Comperve/UFRN"

_SCHOOLS = {
    "escolaagricola": "Escola Agrícola de Jundiaí (UFRN)",
    "escolaenfermagem": "Escola de Enfermagem (UFRN)",
    "escolamusica": "Escola de Música (UFRN)",
    "imd": "Instituto Metrópole Digital (UFRN)",
}


def _school_name(path: str) -> str:
    for key, name in _SCHOOLS.items():
        if key in path:
            return name
    return "Curso técnico (UFRN)"


def parse(html: str) -> List[Opportunity]:
    soup = BeautifulSoup(html, "html.parser")
    by_process: Dict[str, Opportunity] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/cursostecnicos/" not in href:
            continue
        # Um processo seletivo = uma pasta; vários avisos apontam para ela.
        process_url = urljoin(URL, re.sub(r"[^/]+\.php$", "informacoes.php", href))
        notice = a.get_text(" ", strip=True)
        if process_url in by_process:
            continue
        by_process[process_url] = Opportunity(
            title=f"Curso técnico: processo seletivo da {_school_name(href)}",
            url=process_url,
            source=NAME,
            summary=f"Último aviso: {notice}" if len(notice) > 20 else "",
        )
    return list(by_process.values())


def fetch() -> List[Opportunity]:
    return parse(http.get(URL).text)
