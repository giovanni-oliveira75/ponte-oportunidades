from datetime import date

from crawler.classify import categorize, extract_deadline, is_relevant, parse_br_date
from crawler.sources import ifrn
from crawler.sources.wordpress import WordPressSource

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
    items = ifrn.parse(html)
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
