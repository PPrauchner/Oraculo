*[English version](CLAUDE.en.md)*

# CLAUDE.md — ORÁCULO

Ferramenta de auditoria de dependências Python (Streamlit). Recebe um Projeto-Alvo, cruza
o que ele **declara** com o que ele **importa**, consulta o PyPI e reporta Zumbis,
Fantasmas e Desatualizadas.

Trabalho acadêmico (RP III, Marco I) — o [enunciado](./docs/Enunciado.md) é o contrato:
requisitos vêm de lá, não de intuição de produto.

## Leia antes de implementar

| Arquivo | O que é |
|---|---|
| [`CONTEXT.md`](./CONTEXT.md) | **Glossário do domínio.** Zumbi, Fantasma, Versão Usada, Tamanho, Idade têm definição exata. Use esses termos. |
| [`docs/adr/`](./docs/adr/) | **Por que** as decisões não-óbvias são como são. Leia antes de "consertar" algo que parece errado. |
| [`docs/Enunciado.md`](./docs/Enunciado.md) | Requisitos e histórias de usuário (US-01…US-07). |
| [`.claude/rules/`](./.claude/rules/) | Convenções de código, Python e princípios de trabalho. |

## Stack e comandos

Python ≥3.11, gerenciado por **uv**. Streamlit multipage via `st.navigation`.

```bash
uv sync                        # instalar dependências
uv run streamlit run main.py   # rodar a aplicação
uv run pytest                  # rodar os testes
```

## Arquitetura

Pipeline procedural (Regra 01 do enunciado: **paradigma procedural** — sem classes de
domínio). `pages/loading.py` orquestra; `core/` tem as etapas; nada em `core/` importa
`streamlit`.

```
main.py                 navegação Streamlit
pages/                  UI — home (entrada), loading (orquestra o pipeline), report (US-06/07)
core/ingestion/         abrir o Projeto-Alvo e filtrar Exclusões
core/parsin/            ler Declarações/Lock (readers) e extrair Imports Raiz (import_parser)
core/analysis/          classificar Zumbis, Fantasmas, Desatualizadas
core/pypi/              cliente da API pública do PyPI
core/report/            consolidar e exportar (CSV)
utils/                  constantes, sidebar, registries de funções
utils/display.py        veste o dado do relatório na língua da tela
utils/messages.py       veste o código de erro de `core/` na língua da tela
```

**Registries.** `utils/functions.py` expõe o decorador `registrar` e dois dicionários:
`EXTRATORES` (extensão → função que abre o arquivo) e `READERS` (nome de arquivo → parser).
Suportar um novo formato = escrever a função e decorá-la; nenhum `if` novo em `pages/`.
Cuidado: o registry só popula se o módulo for importado — por isso `pages/loading.py` faz
`import core.parsin.readers` sem usá-lo aparentemente.

**Estado.** Passa por `st.session_state` entre as páginas (`archive`, `ignore_folders`,
`all_dependencies`, `zombies`, `ghosts`, `analysis_complete`). Um rerun do Streamlit
reexecuta a página inteira de cima a baixo.

## Invariantes

Consequências das decisões nos ADRs. Violar isso é regressão, não estilo:

- **Lock nunca define o conjunto auditado**, só resolve versões (ADR-0002). Ler `uv.lock`
  como Declaração faz toda transitiva virar Zumbi.
- **Dependência de Desenvolvimento nunca é Zumbi** (ADR-0003). `ruff`/`mypy` não são
  importados por ninguém, e `pytest` vive nas Exclusões.
- **Módulo Próprio nunca é Fantasma.** `core`, `utils` e `pages` são do Projeto-Alvo, não
  do PyPI.
- **Tamanho e Idade vêm do PyPI, não do disco** (ADR-0004) — precisam dar o mesmo número
  nos dois modos de ingestão (ADR-0001).
- **Nome de Import ≠ Nome de Distribuição.** Sem resolver o Alias, um pacote vira Fantasma
  e Zumbi ao mesmo tempo. `.lower().replace("-","_")` não basta.
- **Não inventar Versão Usada.** Sem Lock e sem pin, Idade/Tamanho são indisponíveis —
  reportar o Indeterminado (`UNKNOWN`), nunca assumir a versão do PyPI. Ele não se
  confunde com o Não Aplicável (`N/A`, a Origem de um Fantasma): "não sabemos" e "não se
  aplica" são problemas diferentes, e só o primeiro melhora com um Lock.
- **`core/` não conhece Streamlit — nem a língua da tela.** O retorno é um **código
  estável em inglês mais os dados que o descrevem** — `("directory_not_found", {"path":
  ...})` —, nunca frase pronta nem emoji (ADR-0010). Vale para o erro e para o dado: o
  relatório sai em bytes e dias, não em "1.2 MB" e "30 dias". Ícone, unidade, redação e
  língua são de quem renderiza — `utils/messages.py` para os erros, `utils/display.py`
  para o relatório.
- **Identidade não é rótulo.** Categoria, Status e Origem são comparados, não só
  exibidos: `dep["status"] == STATUS_OUTDATED` decide a coluna Outdated do CSV e a aba
  Desatualizadas. Traduzir o valor junto com o texto quebra as comparações em silêncio.
  Identidade em inglês em `utils/constants.py`; rótulo por `t()` na renderização.

## Armadilhas conhecidas

- O ORÁCULO **é um Projeto-Alvo válido** — use-o para testar. Hoje ele passa na própria
  auditoria: sem Fantasmas (issue #28) e sem Zumbis (issue #32). O log da sessão de grill
  em `docs/grills_logs/` descreve a auditoria antiga, que ainda reprovava.
- `tests/integration/test_self_audit.py` guarda esse estado: mexer na Declaração do
  `pyproject.toml` sem mexer nos imports quebra o teste de Fantasma ou o de Zumbi. Antes de
  declarar um pacote novo, importe-o de fato; ao parar de importar, tire-o da Declaração.
- Nome do produto é **ORÁCULO** (Organizador e Rastreador Automático de Código, Uso de
  Libraries e Ocorrências). `Baita Auditor` e `DP-Auditor` são nomes antigos; `problema-01`
  nunca foi nome de produto, só pasta de trabalho. Documentação e código já usam o nome
  novo (issues #23, #24, #31) — o nome antigo só sobrevive de propósito em
  `docs/grills_logs/`, que é registro histórico point-in-time.
