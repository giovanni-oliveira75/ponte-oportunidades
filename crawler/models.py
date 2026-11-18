"""Modelo de dados de uma oportunidade coletada."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class Opportunity:
    title: str
    url: str                         # página de detalhes (edital, matéria, página oficial)
    source: str                      # nome amigável da fonte (ex.: "IFRN")
    category: str = "Outras"         # preenchida pelo classificador
    deadline: Optional[str] = None   # ISO yyyy-mm-dd, quando a fonte informa
    published: Optional[str] = None  # ISO yyyy-mm-dd
    summary: str = ""
    apply_url: Optional[str] = None  # link direto de inscrição/cadastro, quando existe
    apply_label: str = "Inscrever-se"
    highlights: List[str] = field(default_factory=list)  # ex.: "40 vagas", "Gratuito", "Parnamirim"
    near: bool = False               # acontece em Parnamirim/Natal (perto da escola)
    evergreen: bool = False          # links fixos (Enem, Sisu...) que não vencem
    link_ok: Optional[bool] = None   # preenchido pela verificação de links
    id: str = field(default="")

    def __post_init__(self) -> None:
        self.title = " ".join(self.title.split())
        self.summary = " ".join(self.summary.split())
        if not self.id:
            self.id = hashlib.sha1(self.url.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        return asdict(self)
