# Grill — Lacunas do Marco I (2026-07-16)

Sessão de `grill-with-docs` para levantar o que falta implementar e o que precisa ser
corrigido, confrontando o código com o [enunciado](../Enunciado.md).

Resultado: `CONTEXT.md` criado (glossário), ADRs 0001–0004 registrados, `CLAUDE.md`
preenchido. O backlog abaixo é o que sobrou para implementar.

## Decisões desta sessão

| Questão | Decisão | Onde ficou |
|---|---|---|
| US-01 diz "diretório", código faz upload | Suportar os dois | ADR-0001 |
| O que é "Tamanho"? | Bytes do wheel/sdist da Versão Usada, via PyPI | ADR-0004, `CONTEXT.md` |
| Qual é a "versão usada" se não é pinada? | Declaração = conjunto, Lock = versão | ADR-0002 |
| `import yaml` ≠ `PyYAML` | Tabela de aliases em `constants.py` | `CONTEXT.md` (Alias de Import) |
| `core`/`utils` viram Fantasmas | Inferir Módulo Próprio do layout | `CONTEXT.md` (Módulo Próprio) |
| Esquema do CSV | Uma linha por dependência + Data + Categoria | Backlog F3 |
| Várias Declarações | Unir todas, preservando a Origem | ADR-0002, ADR-0003 |
| Dev deps viram Zumbis | Dependência de Desenvolvimento é isenta | ADR-0003 |
| Busca no PyPI | 1 request/pacote em `/pypi/NAME/json` | ADR-0004 |
| Três nomes para o produto | **Baita Auditor** | `CLAUDE.md` |

## Backlog — falta implementar

**F1. Parsear `pyproject.toml`.** `READERS` registra `requirements.txt`, `environment.yml`
e `.lock` — o enunciado cita `pyproject.toml` primeiro, no objetivo e na Regra 02. Ler
`[project].dependencies` (Produção) e `[dependency-groups]`/`[project.optional-dependencies]`
(Desenvolvimento), preservando a Origem. Bloqueia F5 e o ADR-0003.

**F2. Tamanho e Idade.** Não existem em lugar nenhum do código. `get_latest_version`
descarta `releases[versão]`, que já traz `size` e `upload_time` na mesma resposta. Exigidos
pelo enunciado para as três categorias e nomeados na US-06. Maior lacuna da entrega.

**F3. Reescrever o esquema do CSV.** Hoje exporta `Pacote`/`Versão Atual`/`Versão PyPI`/
`Status`: sem coluna de Categoria (um CSV de zumbis+fantasmas não distingue as linhas —
US-06 pede estratificação) e sem Data (dois relatórios de semanas diferentes ficam
idênticos — a US-07 existe só para isso). Alvo: `Data da Análise, Projeto, Pacote,
Categoria, Origem, Versão Usada, Versão PyPI, Desatualizada, Tamanho, Idade`.

**F4. Ingestão por diretório** (ADR-0001). Exige abstrair a fonte de arquivos: hoje
`filter.py` e `import_parser.py` falam `ZipInfo`/`TarInfo` direto.

**F5. Ler o Lock para resolver Versão Usada** (ADR-0002). O parser de `.lock` já existe —
falta usá-lo como fonte de versões em vez de fonte de conjunto.

**F6. Estatísticas por categoria** (US-06). O relatório mostra contagem; faltam Tamanho
total e Idade média estratificados por categoria. Depende de F2.

## Backlog — falta corrigir

**C1. `_find_dependency_file` devolve o primeiro arquivo que casar**
([`pages/loading.py`](../../pages/loading.py)). Num projeto uv, lê `uv.lock` e reporta toda
transitiva como Zumbi. Viola o ADR-0002. **Mais grave da lista** — corrompe a US-03 inteira.

**C2. Módulo Próprio classificado como Fantasma.** `is_valid_import` rejeita só stdlib e
`_`-prefixados; o guard de import relativo (`node.level == 0`) não pega
`from core.pypi.pypi_client import ...`. Auditar este projeto reporta `core` e `utils` como
Fantasmas.

**C3. Alias de Import não resolvido.** `.lower().replace("-","_")` nos dois analisadores.
Cada mismatch gera um Fantasma **e** um Zumbi.

**C4. Versão Usada inventada.** `outdated_analizer.py` copia a versão do PyPI para
`Versão Atual` quando não há versão declarada e marca "Atualizado" — reporta como atualizado
algo cuja versão não se conhece. Viola o ADR-0002.

**C5. O próprio projeto reprova na auditoria.** `pyproject.toml` não declara `requests` nem
`packaging` (usados em `pypi_client.py` e `outdated_analizer.py`); declara `altair`, que
ninguém importa. Funciona só porque `streamlit` arrasta as duas como transitivas.

**C6. Cores do donut nunca aplicam.** As chaves de `MAPA_CORES_STATUS` têm espaço à
esquerda (`" Zumbis 🧟"`) e não casam com os rótulos do gráfico (`"Zumbis"`). Cai no default
do Plotly, silenciosamente.

**C7. `_extract_version_number` pega a versão errada.** Em `!=1.25.0,>=1.21.1` o regex
retorna `1.25.0` — exatamente a versão excluída. Some com F5/ADR-0002 (a versão passa a vir
do Lock), mas o fallback continua no código.

**C8. `_render_loading_ui` está definida duas vezes** em `pages/loading.py`; a primeira é
morta. Só ruído, mas ruído que engana quem lê.

**C9. Documentação desatualizada.** O README ainda descreve a árvore sob `problema-01/`
(a pasta foi achatada para a raiz), chama o produto de DP-Auditor e omite `pyproject.toml`
da tabela de formatos suportados.

## Ordem sugerida

1. **C1** — sozinho, distorce todo o relatório.
2. **F1** — destrava a Origem, base do ADR-0003.
3. **C2, C3, C5** — eliminam os falsos positivos das US-03/US-04.
4. **F2** — a lacuna mais visível na avaliação.
5. **F3, F6** — fecham US-06/US-07.
6. **F4, F5** — ingestão e resolução de versão.
7. **C4, C6, C7, C8, C9** — arestas.
