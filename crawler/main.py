"""Executa a coleta completa: fontes -> filtro -> classificação -> links -> JSON, métricas e página.

Uso: python -m crawler.main
"""
from __future__ import annotations

import csv
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from crawler import http
from crawler.classify import categorize, is_relevant, normalize
from crawler.models import Opportunity
from crawler.render import render
from crawler.sources import SOURCES

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "opportunities.json"
HISTORY_FILE = ROOT / "data" / "history.csv"
PAGE_FILE = ROOT / "docs" / "index.html"
MAX_AGE_WITHOUT_DEADLINE = 21  # dias: notícia sem prazo claro sai do mural depois disso

log = logging.getLogger("crawler")


def collect() -> Tuple[List[Opportunity], Dict[str, str]]:
    items: List[Opportunity] = []
    status: Dict[str, str] = {}
    for name, fetch in SOURCES:
        try:
            found = fetch()
            items.extend(found)
            status[name] = f"ok ({len(found)})"
            log.info("%s: %d itens", name, len(found))
        except Exception as exc:  # uma fonte fora do ar não derruba as outras
            status[name] = f"falhou: {type(exc).__name__}"
            log.warning("%s falhou: %s", name, exc)
    return items, status


def curate(items: List[Opportunity], today: date) -> List[Opportunity]:
    seen, kept = set(), []
    cutoff = (today - timedelta(days=MAX_AGE_WITHOUT_DEADLINE)).isoformat()
    for opp in items:
        title_key = normalize(opp.title)
        if opp.url in seen or title_key in seen:
            continue  # mesma notícia publicada em dois sites (ex.: SENAI e FIERN)
        seen.update({opp.url, title_key})
        if not opp.evergreen:
            if not is_relevant(opp.title, opp.summary):
                continue
            if opp.deadline and opp.deadline < today.isoformat():
                continue  # prazo vencido
            if not opp.deadline and opp.published and opp.published < cutoff:
                continue  # notícia antiga sem prazo
            opp.category = categorize(opp.title, opp.summary)
        kept.append(opp)
    # Com prazo primeiro (mais urgente no topo), depois mais recentes, depois links fixos.
    kept.sort(key=lambda o: o.published or "", reverse=True)
    kept.sort(key=lambda o: (o.evergreen, o.deadline or "9999"))  # sort estável
    return kept


def check_links(items: List[Opportunity]) -> None:
    with ThreadPoolExecutor(max_workers=8) as pool:
        for opp, ok in zip(items, pool.map(lambda o: http.check_link(o.url), items)):
            opp.link_ok = ok


def append_history(items: List[Opportunity], status: Dict[str, str], now: datetime) -> dict:
    total = len(items)
    dynamic = [o for o in items if not o.evergreen]
    valid = sum(1 for o in items if o.link_ok)
    row = {
        "executado_em": now.strftime("%Y-%m-%d %H:%M"),
        "total": total,
        "coletadas_automaticamente": len(dynamic),
        "links_validos_pct": round(100 * valid / total, 1) if total else 0,
        "fontes_ok": sum(1 for s in status.values() if s.startswith("ok")),
        "fontes_total": len(status),
        "detalhe_fontes": "; ".join(f"{k}={v}" for k, v in status.items()),
    }
    new_file = not HISTORY_FILE.exists()
    with HISTORY_FILE.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row))
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    return row


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    now = datetime.now(timezone(timedelta(hours=-3)))  # horário de Brasília
    raw, status = collect()
    items = curate(raw, now.date())
    check_links(items)
    # Link quebrado não aparece para o aluno (mas entra na métrica).
    visible = [o for o in items if o.link_ok or o.evergreen]

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "atualizado_em": now.isoformat(timespec="minutes"),
        "fontes": status,
        "oportunidades": [o.to_dict() for o in visible],
    }
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    metrics = append_history(items, status, now)
    PAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PAGE_FILE.write_text(render(visible, now, status), encoding="utf-8")

    log.info("Publicadas %d oportunidades | métricas: %s", len(visible), metrics)
    return 0 if metrics["fontes_ok"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
