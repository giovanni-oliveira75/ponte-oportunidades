"""Lista branca de fontes. Só entra aqui site oficial ou institucional: é a defesa contra golpes."""
from crawler.sources import comperve, fixed, ifrn
from crawler.sources.wordpress import WordPressSource

_senai = WordPressSource("SENAI-RN", "https://www.rn.senai.br",
                         searches=["inscrições", "cursos gratuitos", "vagas"])
_fiern = WordPressSource("FIERN (SESI/SENAI/IEL)", "https://www.fiern.org.br",
                         searches=["jovem aprendiz", "estágio", "inscrições"])
_govrn = WordPressSource("Governo do RN", "https://www.rn.gov.br", post_type="materia",
                         searches=["inscrições abertas", "jovem aprendiz", "cursos gratuitos", "vagas de emprego"])
_sethas = WordPressSource("SETHAS/SINE-RN", "https://www.sethas.rn.gov.br", post_type="materia",
                          searches=["vagas", "sine", "qualificação"])

# (nome, função de coleta)
SOURCES = [
    ("IFRN", ifrn.fetch),
    ("Comperve/UFRN", comperve.fetch),
    (_senai.name, _senai.fetch),
    (_fiern.name, _fiern.fetch),
    (_govrn.name, _govrn.fetch),
    (_sethas.name, _sethas.fetch),
    ("Links oficiais", fixed.fetch),
]
