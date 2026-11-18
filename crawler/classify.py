"""Regras de relevância e categorização para alunos do 3º ano do ensino médio."""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Optional

CATEGORIES = [
    "Jovem Aprendiz e Estágio",
    "Emprego",
    "Cursos Técnicos e Gratuitos",
    "Ensino Superior",
    "Outras",
]

# Ordem importa: a primeira regra que casar define a categoria.
_RULES = [
    ("Jovem Aprendiz e Estágio", r"aprendiz|estagi"),
    ("Ensino Superior", r"enem|sisu|prouni|fies|vestibular|graduacao|licenciatura|tecnologo|bacharelado"),
    ("Cursos Técnicos e Gratuitos", r"tecnic|curso|qualifica|capacita|formacao inicial|fic\b|gratuit|bolsa"),
    ("Emprego", r"vaga|emprego|sine|contrata|selecao"),
]

# Itens que não servem para quem está terminando o ensino médio.
_EXCLUDE = re.compile(
    r"pos-graduacao|pos graduacao|mestrado|doutorado|especializacao|lato sensu|stricto"
    r"|professor|docente|servidor|eja\b|modalidade eja|concurso publico|licitacao|resultado final"
    r"|gabarito|homologa|convocacao para a defesa|exclusivo para servidores"
    # público empresarial, não estudantil
    r"|empresari|industriais|aduaneir|licenciamento|exportac|importac|sindicato patronal"
    # notícia de algo que já aconteceu
    r"|\bconclui|\bencerra|realizou|formou turma|certifica turma|forma turma"
)

# Para fontes de notícias: só entra se falar de algo em que o aluno pode se inscrever.
_OPPORTUNITY_SIGNAL = re.compile(
    r"inscri|vagas?\b|edital|seletivo|aprendiz|estagi|bolsas?\b|matricula"
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def is_relevant(title: str, summary: str = "", require_signal: bool = False) -> bool:
    text = normalize(f"{title} {summary}")
    if _EXCLUDE.search(text):
        return False
    if require_signal and not _OPPORTUNITY_SIGNAL.search(normalize(title)):
        return False
    return True


def categorize(title: str, summary: str = "") -> str:
    text = normalize(f"{title} {summary}")
    for category, pattern in _RULES:
        if re.search(pattern, text):
            return category
    return "Outras"


_DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?")


def parse_br_date(text: str, today: Optional[date] = None) -> Optional[date]:
    """Converte '21/12/2026' ou '21/12' em date. Sem ano, assume o próximo dia/mês futuro."""
    today = today or date.today()
    m = _DATE_RE.search(text)
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), m.group(3)
    if year:
        y = int(year)
        y = y + 2000 if y < 100 else y
    else:
        y = today.year
    try:
        d = date(y, month, day)
    except ValueError:
        return None
    if not year and d < today:
        try:
            d = date(y + 1, month, day)
        except ValueError:
            return None
    return d


def extract_deadline(text: str, today: Optional[date] = None) -> Optional[date]:
    """Procura um prazo do tipo 'até 30/11' ou '03/11/2026 até 21/12/2026'."""
    norm = normalize(text)
    m = re.search(r"ate\s+(?:o\s+dia\s+)?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)", norm)
    if m:
        return parse_br_date(m.group(1), today)
    return None
