# Ponte para Oportunidades

Mural digital e autossuficiente de oportunidades de estudo e trabalho para jovens do ensino médio do RN.
É desenvolvido como projeto de extensão universitária (Ciência da Computação, UNP; programa
*Governança e Justiça Social*) em parceria com a **EE Dr. Antônio de Souza** (Parnamirim/RN).

Os alunos acessam pelo celular, via QR Code. Um robô (crawler) coleta as informações todo dia, apenas de
**fontes oficiais**, então ninguém na escola precisa atualizar o mural.

## Hipótese

> Se as oportunidades forem reunidas em um canal digital único, de baixo custo, acessível por QR Code e
> atualizado automaticamente a partir de fontes confiáveis, e se isso vier junto com uma orientação
> prática sobre cadastro e segurança, então os alunos vão conhecer mais oportunidades, se sentir mais
> seguros para se inscrever, e o canal vai continuar atualizado sem depender de pessoas.

| Sub-hipótese | Indicador | Onde medir |
|---|---|---|
| H1a: centralizar reduz o tempo para encontrar uma oportunidade | taxa de sucesso e tempo na tarefa "encontre uma vaga de Jovem Aprendiz" | teste de usabilidade na aula |
| H1b: a orientação melhora a capacidade de se cadastrar e de reconhecer golpes | % antes e depois | questionário pré e pós |
| H1c: a automação mantém o canal atualizado sem intervenção humana | execuções diárias bem-sucedidas, itens coletados, % de links válidos | `data/history.csv` |

## Como funciona

```
GitHub Actions (todo dia, 06h)
  -> crawler/sources/*   coleta na lista branca de fontes oficiais
  -> entra em cada edital/matéria e extrai vagas, campus, prazo e o link direto de inscrição
  -> crawler/classify.py filtra o que serve ao 3º ano, categoriza e marca o que é perto (Parnamirim/Natal)
  -> crawler/http.py     respeita robots.txt, espaça requisições e verifica links
  -> data/opportunities.json + data/history.csv (métricas)
  -> docs/index.html     página publicada no GitHub Pages (template em crawler/template.html)
```

**Fontes (lista branca):** IFRN (processos seletivos), Comperve/UFRN (cursos técnicos), SENAI-RN, FIERN
(SESI/SENAI/IEL), Governo do RN, SETHAS/SINE-RN, mais links oficiais permanentes (Enem, Sisu, Prouni,
Fies, CIEE, IEL, SENAC, Escola Virtual Gov) em `sources_fixed.yaml`.

**Segurança contra golpes:** o robô nunca coleta de sites abertos de vagas. Só entra fonte oficial ou
institucional. Itens vencidos e links quebrados são removidos automaticamente.

**Custo:** zero (GitHub Actions + GitHub Pages).

## Rodar localmente

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m crawler.main      # gera data/ e docs/index.html
open docs/index.html
```

## Adicionar uma fonte

- Site WordPress oficial: uma linha em `crawler/sources/__init__.py` com `WordPressSource(...)`.
- Link fixo: uma entrada em `sources_fixed.yaml`.
- Outro formato: um módulo em `crawler/sources/` com uma função `fetch()` que devolve `List[Opportunity]`.
