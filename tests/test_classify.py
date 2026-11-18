from datetime import date

from crawler.classify import categorize, extract_deadline, is_relevant, parse_br_date
from crawler.models import Opportunity
from crawler.sources import comperve, ifrn
from crawler.sources.wordpress import WordPressSource, find_apply_link

TODAY = date(2026, 11, 18)


def test_excludes_items_not_for_high_school():
    assert not is_relevant("EDITAL Nº 62/2026 Pós-Graduação Lato Sensu a Distância")
    assert not is_relevant("Cursos Técnicos na Forma Integrada (Modalidade EJA)")
    assert not is_relevant("Capacitação sobre regime aduaneiro para empresários")
    assert is_relevant("Cursos Técnicos de Nível Médio na Forma Subsequente 2027.1")


def test_news_needs_opportunity_signal():
    assert not is_relevant("SENAI-RN participa de feira da indústria", require_signal=True)
    assert is_relevant("SENAI abre inscrições para cursos gratuitos", require_signal=True)


def test_categories():
    assert categorize("Programa Jovem Aprendiz abre vagas") == "Jovem Aprendiz e Estágio"
    assert categorize("Inscrições do Sisu 2027") == "Ensino Superior"
    assert categorize("Curso técnico gratuito em eletrotécnica") == "Cursos Técnicos e Gratuitos"
    assert categorize("Sine-RN oferece 60 vagas em Natal") == "Emprego"


def test_dates():
    assert parse_br_date("21/12/2026") == date(2026, 12, 21)
    assert parse_br_date("10/01", TODAY) == date(2027, 1, 10)  # sem ano: próxima ocorrência
    assert extract_deadline("Inscrições vão até o dia 30/11", TODAY) == date(2026, 11, 30)
    assert extract_deadline("Sem prazo informado", TODAY) is None


def test_ifrn_parser_reads_open_editais():
    html = """
    <div class="box12 success"><h2>Inscrições Abertas</h2><div class="content"><table><tbody>
      <tr><td><h3><a href='/edital/visualizar/700/'>EDITAL Nº 59/2026 Cursos Técnicos Subsequentes</a></h3></td>
          <td>10/11/2026 até 05/12/2026</td><td></td></tr>
    </tbody></table></div></div>
    <div class="box12"><h2>Em andamento</h2><table><tbody>
      <tr><td><h3><a href='/edital/visualizar/1/'>Edital antigo</a></h3></td><td>-</td></tr>
    </tbody></table></div>"""
    items = ifrn.parse_list(html)
    assert len(items) == 1
    assert items[0].deadline == "2026-12-05"
    assert items[0].url == "https://processoseletivo.ifrn.edu.br/edital/visualizar/700/"


def test_wordpress_parser_filters_and_extracts_deadline():
    src = WordPressSource("Teste", "https://exemplo.gov.br")
    posts = [
        {"title": {"rendered": "Inscri&ccedil;&otilde;es abertas para Jovem Aprendiz at&eacute; 30/11"},
         "excerpt": {"rendered": "<p>Vagas em Natal</p>"}, "link": "https://exemplo.gov.br/a", "date": "2026-11-10T10:00:00"},
        {"title": {"rendered": "Governador visita obra"}, "excerpt": {"rendered": ""},
         "link": "https://exemplo.gov.br/b", "date": "2026-11-10T10:00:00"},
    ]
    items = src.parse(posts, TODAY)
    assert [i.url for i in items] == ["https://exemplo.gov.br/a"]
    assert items[0].deadline == "2026-11-30"


def test_ifrn_enrich_prefers_nearby_campus_and_counts_vagas():
    html = """
    <table><tbody>
      <tr><td>Ceará-Mirim</td><td>Técnico em Informática</td><td>Noturno</td><td>40</td>
          <td><a href='/inscricao/wizard/1/700/'>Realizar inscrição</a></td></tr>
      <tr><td>Parnamirim</td><td>Técnico em Informática</td><td>Noturno</td><td>36</td>
          <td><a href='/inscricao/wizard/2/700/'>Realizar inscrição</a></td></tr>
    </tbody></table><p>Taxa de inscrição: Gratuita</p>"""
    opp = ifrn.enrich(Opportunity(title="Edital", url="https://processoseletivo.ifrn.edu.br/edital/visualizar/700/",
                                  source="IFRN"), html)
    assert opp.apply_url.endswith("/inscricao/wizard/2/700/")
    assert opp.near and "76 vagas" in opp.highlights and "Gratuito" in opp.highlights


def test_find_apply_link_skips_social_and_internal_links():
    content = """<p>Veja <a href="https://www.fiern.org.br/outra-noticia/">outra</a>,
      siga no <a href="https://instagram.com/x">Instagram</a> e
      <a href="https://www.sympla.com.br/evento/123">faça sua inscrição</a>.</p>"""
    assert find_apply_link(content, "fiern.org.br") == "https://www.sympla.com.br/evento/123"


def test_comperve_short_title():
    official = ("PROCESSO SELETIVO 2026 PARA OS CURSOS TÉCNICOS DE NÍVEL MÉDIO NAS FORMAS SUBSEQUENTE "
                "E CONCOMITANTE – INGRESSO NO ANO LETIVO DE 2027 - 11/2026")
    assert comperve.short_title(official, "Escola Agrícola de Jundiaí (UFRN)") == \
        "Cursos técnicos subsequentes 2027: Escola Agrícola de Jundiaí (UFRN)"
