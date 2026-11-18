"""Gera a página estática (docs/index.html), pensada para celular e acesso por QR Code."""
from __future__ import annotations

from datetime import date, datetime
from html import escape
from typing import Dict, List

from crawler.classify import CATEGORIES
from crawler.models import Opportunity

SCHOOL = "EE Dr. Antônio de Souza"


def _fmt(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def _card(o: Opportunity, today: date) -> str:
    badge = ""
    if o.deadline:
        days = (date.fromisoformat(o.deadline) - today).days
        urgent = " urgent" if days <= 7 else ""
        when = "último dia: hoje" if days == 0 else f"inscrições até {_fmt(o.deadline)}"
        badge = f'<span class="badge{urgent}">{when}</span>'
    elif o.published and not o.evergreen:
        badge = f'<span class="badge muted">publicado em {_fmt(o.published)}</span>'
    summary = f"<p>{escape(o.summary)}</p>" if o.summary else ""
    search = escape(f"{o.title} {o.summary} {o.source}".lower(), quote=True)
    return f"""
    <article class="card" data-cat="{escape(o.category, quote=True)}" data-search="{search}">
      <div class="meta"><span class="tag">{escape(o.category)}</span>{badge}</div>
      <h2>{escape(o.title)}</h2>
      {summary}
      <div class="foot">
        <span class="src">Fonte: {escape(o.source)}</span>
        <a href="{escape(o.url, quote=True)}" target="_blank" rel="noopener">Abrir site oficial</a>
      </div>
    </article>"""


def render(items: List[Opportunity], now: datetime, status: Dict[str, str]) -> str:
    today = now.date()
    present = [c for c in CATEGORIES if any(o.category == c for o in items)]
    chips = '<button class="chip on" data-filter="">Todas</button>' + "".join(
        f'<button class="chip" data-filter="{escape(c, quote=True)}">{escape(c)}</button>' for c in present
    )
    cards = "".join(_card(o, today) for o in items) or "<p>Nenhuma oportunidade no momento.</p>"
    fontes = "".join(f"<li>{escape(k)}: {escape(v)}</li>" for k, v in status.items())
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ponte para Oportunidades</title>
<meta name="description" content="Oportunidades de estudo e trabalho para jovens do RN, coletadas automaticamente de fontes oficiais.">
<style>
:root {{ --bg:#f6f7fb; --card:#fff; --ink:#1d2433; --muted:#5b6475; --line:#e3e6ee;
  --brand:#1f5fbf; --brand-ink:#fff; --warn:#b42318; --warn-bg:#fdecea; --tag:#e8f0fd; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0f141c; --card:#171e29; --ink:#e7ebf2;
  --muted:#9aa4b5; --line:#263041; --brand:#6aa3ff; --brand-ink:#0f141c; --warn:#ff8a7a;
  --warn-bg:#3a1d1a; --tag:#1d2b42; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
header {{ background:var(--brand); color:var(--brand-ink); padding:20px 16px 16px; }}
header h1 {{ margin:0; font-size:1.5rem; }}
header p {{ margin:4px 0 0; opacity:.9; font-size:.9rem; }}
main {{ max-width:760px; margin:0 auto; padding:16px; }}
.alert {{ background:var(--warn-bg); color:var(--ink); border-left:4px solid var(--warn);
  border-radius:8px; padding:12px 14px; margin-bottom:16px; font-size:.92rem; }}
.alert strong {{ color:var(--warn); }}
.alert ul {{ margin:6px 0 0; padding-left:18px; }}
input[type=search] {{ width:100%; padding:12px 14px; border:1px solid var(--line); border-radius:10px;
  background:var(--card); color:var(--ink); font-size:1rem; }}
.chips {{ display:flex; gap:8px; overflow-x:auto; padding:12px 0; }}
.chip {{ flex:none; border:1px solid var(--line); background:var(--card); color:var(--ink);
  border-radius:999px; padding:6px 12px; font-size:.85rem; cursor:pointer; }}
.chip.on {{ background:var(--brand); color:var(--brand-ink); border-color:var(--brand); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; margin-bottom:12px; }}
.card h2 {{ font-size:1.02rem; margin:8px 0 6px; }}
.card p {{ margin:0 0 8px; color:var(--muted); font-size:.92rem; }}
.meta {{ display:flex; flex-wrap:wrap; gap:6px; }}
.tag,.badge {{ font-size:.75rem; border-radius:6px; padding:2px 8px; }}
.tag {{ background:var(--tag); color:var(--brand); }}
.badge {{ border:1px solid var(--line); }}
.badge.urgent {{ border-color:var(--warn); color:var(--warn); font-weight:600; }}
.badge.muted {{ color:var(--muted); }}
.foot {{ display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap; }}
.src {{ font-size:.8rem; color:var(--muted); }}
.foot a {{ background:var(--brand); color:var(--brand-ink); text-decoration:none; padding:8px 12px;
  border-radius:8px; font-size:.88rem; font-weight:600; }}
footer {{ max-width:760px; margin:0 auto; padding:8px 16px 32px; color:var(--muted); font-size:.8rem; }}
footer ul {{ padding-left:18px; }}
</style>
</head>
<body>
<header>
  <h1>Ponte para Oportunidades</h1>
  <p>Estudo e trabalho para jovens do RN · {escape(SCHOOL)}</p>
  <p>Atualizado automaticamente em {now.strftime("%d/%m/%Y às %H:%M")}</p>
</header>
<main>
  <div class="alert"><strong>Vaga de verdade não cobra nada.</strong>
    <ul>
      <li>Desconfie de quem pede Pix, taxa de cadastro ou "kit" para garantir a vaga.</li>
      <li>Não envie foto de documento por WhatsApp para desconhecidos.</li>
      <li>Confira se o site é oficial (gov.br, edu.br, senai, ciee) antes de se cadastrar.</li>
    </ul>
  </div>
  <input type="search" id="q" placeholder="Buscar: técnico, aprendiz, Enem..." aria-label="Buscar oportunidades">
  <nav class="chips" aria-label="Categorias">{chips}</nav>
  <section id="list">{cards}</section>
  <p id="empty" hidden>Nada encontrado com esse filtro.</p>
</main>
<footer>
  <p>Este mural é atualizado todos os dias por um robô que lê apenas sites oficiais. Sempre confirme as
  informações no site da instituição. Projeto de extensão universitária (Ciência da Computação, UNP).</p>
  <details><summary>Situação das fontes nesta atualização</summary><ul>{fontes}</ul></details>
</footer>
<script>
(function () {{
  var q = document.getElementById('q'), cat = '', cards = document.querySelectorAll('.card');
  function apply() {{
    var term = q.value.trim().toLowerCase(), shown = 0;
    cards.forEach(function (c) {{
      var ok = (!cat || c.dataset.cat === cat) && (!term || c.dataset.search.indexOf(term) !== -1);
      c.hidden = !ok; if (ok) shown++;
    }});
    document.getElementById('empty').hidden = shown !== 0;
  }}
  document.querySelectorAll('.chip').forEach(function (b) {{
    b.addEventListener('click', function () {{
      document.querySelectorAll('.chip').forEach(function (x) {{ x.classList.remove('on'); }});
      b.classList.add('on'); cat = b.dataset.filter; apply();
    }});
  }});
  q.addEventListener('input', apply);
}})();
</script>
</body>
</html>
"""
