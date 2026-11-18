"""Cliente HTTP educado: identifica o robô, respeita robots.txt e espaça as requisições."""
from __future__ import annotations

import tempfile
import time
import urllib.robotparser
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse

import certifi
import requests

USER_AGENT = (
    "PonteOportunidadesBot/1.0 (projeto de extensao universitaria UNP; "
    "+https://github.com/giovanni-oliveira75/ponte-oportunidades)"
)
TIMEOUT = 25
DELAY_SECONDS = 1.0

_CERTS_DIR = Path(__file__).resolve().parents[1] / "certs"


def _ca_bundle() -> str:
    """certifi + intermediárias que alguns servidores oficiais não enviam (ex.: RNP/Comperve)."""
    extras = sorted(_CERTS_DIR.glob("*.pem"))
    if not extras:
        return certifi.where()
    bundle = Path(tempfile.gettempdir()) / "ponte_ca_bundle.pem"
    bundle.write_text(Path(certifi.where()).read_text() + "".join(p.read_text() for p in extras))
    return str(bundle)


_session = requests.Session()
_session.verify = _ca_bundle()
_session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"})
_robots: Dict[str, urllib.robotparser.RobotFileParser] = {}
_last_hit: Dict[str, float] = {}


class BlockedByRobots(Exception):
    pass


def _allowed(url: str) -> bool:
    parts = urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    rp = _robots.get(base)
    if rp is None:
        rp = urllib.robotparser.RobotFileParser()
        try:
            resp = _session.get(base + "/robots.txt", timeout=TIMEOUT)
            # Sem robots.txt (404) significa que não há restrições declaradas.
            rp.parse(resp.text.splitlines() if resp.status_code == 200 else [])
        except requests.RequestException:
            rp.parse([])
        _robots[base] = rp
    return rp.can_fetch(USER_AGENT, url)


def get(url: str, **kwargs) -> requests.Response:
    if not _allowed(url):
        raise BlockedByRobots(url)
    host = urlparse(url).netloc
    wait = DELAY_SECONDS - (time.time() - _last_hit.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.time()
    resp = _session.get(url, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp


def check_link(url: str) -> bool:
    """Verifica se um link responde (usado na métrica de links válidos)."""
    try:
        resp = _session.head(url, timeout=15, allow_redirects=True)
        if resp.status_code in (403, 405) or resp.status_code >= 500:
            resp = _session.get(url, timeout=15, stream=True)
        return resp.status_code < 400
    except requests.RequestException:
        return False
