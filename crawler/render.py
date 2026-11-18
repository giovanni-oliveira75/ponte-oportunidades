"""Gera a página estática (docs/index.html): mobile-first, acessada por QR Code."""
from __future__ import annotations

from datetime import date, datetime
from html import escape
from pathlib import Path
from typing import Dict, List

from crawler.classify import CATEGORIES
from crawler.models import Opportunity

SCHOOL = "EE Dr. Antônio de Souza"
TEMPLATE = Path(__file__).with_name("template.html")
SOON_DAYS = 14

ICONS = {
    "Jovem Aprendiz e Estágio": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6"/>',
    "Emprego": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2M3 13h18"/>',
    "Cursos Técnicos e Gratuitos": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M8 7h8M8 11h6"/>',
    "Ensino Superior": '<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/>',
    "Outras": '<circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/>',
}
CAT_CLASS = {
    "Jovem Aprendiz e Estágio": "c-aprendiz",
    "Emprego": "c-emprego",
    "Cursos Técnicos e Gratuitos": "c-cursos",
    "Ensino Superior": "c-superior",
    "Outras": "c-outras",
}
PIN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22s7-6.5 7-12a7 7 0 0 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>'
CLOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>'
SHARE = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/>'
         '<circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/></svg>')


def _icon(category: str) -> str:
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS.get(category, ICONS["Outras"])}</svg>'


def _fmt(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}"


def _countdown(o: Opportunity, today: date) -> str:
    if not o.deadline:
        return ""
    days = (date.fromisoformat(o.deadline) - today).days
    if days <= 0:
        text, cls = "Último dia!", "due urgent"
    elif days == 1:
        text, cls = "Termina amanhã", "due urgent"
    elif days <= 7:
        text, cls = f"Faltam {days} dias", "due urgent"
    else:
        text, cls = f"Até {_fmt(o.deadline)}", "due"
    return f'<span class="{cls}">{CLOCK}{text}</span>'


def _attrs(o: Opportunity) -> str:
    search = escape(f"{o.title} {o.summary} {o.source} {' '.join(o.highlights)}".lower(), quote=True)
    return (f'data-cat="{escape(o.category, quote=True)}" data-near="{int(o.near)}" '
            f'data-search="{search}"')


def _pills(o: Opportunity) -> str:
    pills = []
    if o.near:
        pills.append(f'<span class="pill near">{PIN}Perto de você</span>')
    pills += [f'<span class="pill">{escape(h)}</span>' for h in o.highlights[:4]]
    return f'<div class="pills">{"".join(pills)}</div>' if pills else ""


def _actions(o: Opportunity) -> str:
    title = escape(o.title, quote=True)
    primary = o.apply_url or o.url
    label = o.apply_label if o.apply_url else "Ver no site oficial"
    secondary = ""
    if o.apply_url and o.apply_url != o.url:
        secondary = f'<a class="btn ghost" href="{escape(o.url, quote=True)}" target="_blank" rel="noopener">Detalhes</a>'
    return f"""<div class="actions">
        <a class="btn primary" href="{escape(primary, quote=True)}" target="_blank" rel="noopener">{escape(label)}{ARROW}</a>
        {secondary}
        <button class="btn icon share" type="button" data-title="{title}" data-url="{escape(primary, quote=True)}" aria-label="Compartilhar">{SHARE}</button>
      </div>"""


def _card(o: Opportunity, today: date) -> str:
    summary = f'<p class="summary">{escape(o.summary)}</p>' if o.summary else ""
    meta = escape(o.source)
    if o.published and not o.evergreen:
        meta += f" · publicado em {_fmt(o.published)}"
    return f"""
    <article class="card {CAT_CLASS.get(o.category, 'c-outras')}" {_attrs(o)}>
      <div class="card-top">
        <span class="cat-icon">{_icon(o.category)}</span>
        <span class="cat-name">{escape(o.category)}</span>
        {_countdown(o, today)}
      </div>
      <h3>{escape(o.title)}</h3>
      {_pills(o)}
      {summary}
      <p class="source">{meta}</p>
      {_actions(o)}
    </article>"""


def _soon_card(o: Opportunity, today: date) -> str:
    target = escape(o.apply_url or o.url, quote=True)
    return f"""
    <a class="soon {CAT_CLASS.get(o.category, 'c-outras')}" href="{target}" target="_blank" rel="noopener" {_attrs(o)}>
      {_countdown(o, today)}
      <strong>{escape(o.title)}</strong>
      <span class="soon-src">{escape(o.source)}</span>
    </a>"""


def _tile(o: Opportunity) -> str:
    target = escape(o.apply_url or o.url, quote=True)
    return f"""
    <a class="tile {CAT_CLASS.get(o.category, 'c-outras')}" href="{target}" target="_blank" rel="noopener" {_attrs(o)}>
      <span class="cat-icon">{_icon(o.category)}</span>
      <span class="tile-text"><strong>{escape(o.title)}</strong><small>{escape(o.summary)}</small></span>
      <span class="tile-go">{escape(o.apply_label)}{ARROW}</span>
    </a>"""


def render(items: List[Opportunity], now: datetime, status: Dict[str, str]) -> str:
    today = now.date()
    dynamic = [o for o in items if not o.evergreen]
    fixed = [o for o in items if o.evergreen]
    soon = [o for o in dynamic if o.deadline and (date.fromisoformat(o.deadline) - today).days <= SOON_DAYS]
    present = [c for c in CATEGORIES if any(o.category == c for o in items)]

    chips = '<button class="chip on" data-filter="" type="button">Tudo</button>'
    if any(o.near for o in items):
        chips += f'<button class="chip" data-near="1" type="button">{PIN}Perto de mim</button>'
    chips += "".join(
        f'<button class="chip" data-filter="{escape(c, quote=True)}" type="button">{escape(c)}</button>'
        for c in present
    )
    soon_html = ""
    if soon:
        soon_html = f"""
  <section class="block" id="soon-block">
    <div class="block-head"><h2>Encerrando em breve</h2><span class="count">{len(soon)}</span></div>
    <div class="soon-row">{''.join(_soon_card(o, today) for o in soon)}</div>
  </section>"""
    open_html = "".join(_card(o, today) for o in dynamic) or (
        '<p class="empty-note">Nenhuma oportunidade nova nas fontes oficiais hoje. '
        'Veja os links essenciais abaixo; o robô verifica de novo amanhã cedo.</p>'
    )
    fontes = "".join(
        f'<li><span class="dot {"ok" if v.startswith("ok") else "fail"}"></span>{escape(k)}: {escape(v)}</li>'
        for k, v in status.items()
    )
    replacements = {
        "{{SCHOOL}}": escape(SCHOOL),
        "{{UPDATED}}": now.strftime("%d/%m às %H:%M"),
        "{{N_OPEN}}": str(len(dynamic)),
        "{{N_NEAR}}": str(sum(1 for o in items if o.near)),
        "{{N_SOURCES}}": str(sum(1 for v in status.values() if v.startswith("ok"))),
        "{{CHIPS}}": chips,
        "{{SOON}}": soon_html,
        "{{N_DYNAMIC}}": str(len(dynamic)),
        "{{OPEN}}": open_html,
        "{{FIXED}}": "".join(_tile(o) for o in fixed),
        "{{FONTES}}": fontes,
        "{{YEAR}}": str(today.year),
    }
    html = TEMPLATE.read_text(encoding="utf-8")
    for key, value in replacements.items():
        html = html.replace(key, value)
    return html
