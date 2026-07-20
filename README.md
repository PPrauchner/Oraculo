# ORÁCULO

**O**rganizador e **R**astreador **A**utomático de **C**ódigo, **U**so de **L**ibraries e **O**corrências.

Ferramenta web de auditoria de dependências de projetos Python. Cruza o que um
Projeto-Alvo **declara** depender com o que seu código **realmente importa**, e confronta
ambos com o PyPI para reportar Zumbis, Fantasmas e Desatualizadas.

---

## Documentação

O modelo de domínio não é reexplicado aqui — os termos com inicial maiúscula ao longo
deste README (Projeto-Alvo, Declaração, Lock, Zumbi, Fantasma, Versão Usada, Tamanho,
Idade, Origem) têm definição exata no glossário:

| Documento | O que é |
|---|---|
| [`CONTEXT.md`](./CONTEXT.md) | Glossário do domínio — a definição exata de cada termo. |
| [`docs/adr/`](./docs/adr/) | Registros de decisão: **por que** as escolhas não-óbvias são como são. |
| [`docs/Enunciado.md`](./docs/Enunciado.md) | Requisitos e histórias de usuário (US-01…US-07). |

---

## Funcionalidades

### Categorias da auditoria

- **Zumbis** — Dependências de Produção declaradas que nenhum Import Raiz do código usa.
- **Fantasmas** — Imports Raiz do código que nenhuma Declaração menciona. Funcionam na
  máquina do dev por virem de carona como transitivas, e quebram em outro ambiente.
- **Desatualizadas** — dependências cuja Versão Usada é anterior à última publicada no
  PyPI. Não é uma Categoria excludente: uma dependência pode ser Zumbi **e**
  Desatualizada ao mesmo tempo, então sai em coluna própria.

### Produção vs. Desenvolvimento

Cada pacote carrega a **Origem** — de qual Declaração, e de qual seção dela, ele veio:

| Origem | De onde vem | Vira Zumbi? |
|---|---|---|
| **Produção** | `[project].dependencies`, `[tool.poetry].dependencies`, `requirements.txt`, `environment.yml` | Sim |
| **Desenvolvimento** | `[dependency-groups]`, `[project.optional-dependencies]`, `[tool.poetry.group.*]`, `requirements-dev.txt` | **Nunca** |

Dependência de Desenvolvimento nunca é Zumbi ([ADR-0003](./docs/adr/0003-dependencias-de-desenvolvimento-nunca-sao-zumbis.md)):
ferramentas como `ruff` e `mypy` não são importadas por ninguém, e as demais vivem
justamente nas Exclusões.

### Métricas

- **Tamanho** — bytes do wheel (sdist como fallback) da Versão Usada, conforme publicado
  no PyPI. **Não** é tamanho em disco e não inclui transitivas.
- **Idade** — tempo entre a data de lançamento da Versão Usada no PyPI e hoje. Mede há
  quanto tempo o projeto está parado naquela versão, não a idade do pacote.
- **Índice de Saúde** — proporção de Dependências Declaradas que não são Zumbis,
  Fantasmas nem Desatualizadas.

Tamanho e Idade vêm dos metadados do PyPI, não do disco
([ADR-0004](./docs/adr/0004-tamanho-e-idade-vem-dos-metadados-do-pypi.md)) — uma única
requisição a `/pypi/NAME/json` por pacote traz os três dados. Sem Versão Usada resolvida,
ambos saem como **N/D**: o Oráculo não inventa versão.

### Relatório

- Estatísticas de Tamanho somado e Idade média **estratificadas por Categoria**, com
  aviso de quantas dependências ficaram de fora de cada agregação.
- Exportação em **CSV** e **JSON**.
- Consultas ao PyPI em paralelo, para reduzir o tempo de análise.

---

## Formatos Suportados

O conjunto auditado vem **só das Declarações**; o Lock apenas resolve em que versão cada
item desse conjunto está ([ADR-0002](./docs/adr/0002-declaracao-define-o-conjunto-lock-define-a-versao.md)).

| Arquivo | Gerenciador | Papel |
|---|---|---|
| `pyproject.toml` | PEP 621, Poetry | Declaração — define o conjunto (Produção e Desenvolvimento) |
| `requirements.txt` | pip | Declaração — Produção |
| `requirements-dev.txt` | pip | Declaração — Desenvolvimento |
| `environment.yml` | Conda | Declaração — Produção |
| `uv.lock`, `poetry.lock` (`*.lock`) | uv, Poetry | **Lock** — resolve a Versão Usada; nunca define o conjunto |

Um Projeto-Alvo pode ter várias Declarações, e todas valem: o conjunto é a união delas,
deduplicada por Nome de Distribuição, preservando a Origem.

> **Por que o Lock não define o conjunto:** um `uv.lock` lista centenas de transitivas que
> nenhum código importa. Lê-lo como Declaração faria toda transitiva virar Zumbi.

Adicionar um formato = escrever a função de parsing e decorá-la com `@registrar(READERS, "<arquivo>")`
em `core/parsin/readers.py`. Nenhum `if` novo em `pages/`.

---

## Limitações conhecidas

### Resolução de Alias de Import por tabela

Quando o Nome de Import difere do Nome de Distribuição (`import yaml` ↔ `PyYAML`,
`sklearn` ↔ `scikit-learn`, `cv2` ↔ `opencv-python`, `PIL` ↔ `Pillow`), a correspondência
usa uma tabela fixa de aliases (`IMPORT_ALIASES` em `utils/constants.py`). A tabela cobre
os mismatches mais comuns do ecossistema, mas **não é exaustiva**: um pacote com nomes
divergentes que não esteja na tabela ainda gera **dois falsos positivos** — vira Fantasma
(o import não casa com nenhuma declaração) **e** Zumbi (a declaração não casa com nenhum
import) ao mesmo tempo. Mitigação consciente, não solução completa; ampliar a tabela
resolve caso a caso.

### PyYAML é exigido mesmo sem `environment.yml`

`core/parsin/readers.py` importa `yaml` no topo do módulo, e `declaration_collector`
importa `readers` para popular o registry — então o `PyYAML` entra em toda análise, mesmo
quando o Projeto-Alvo não tem `environment.yml`. Por isso ele é Dependência de Produção
declarada: sem ele a aplicação não sobe, em vez de apenas perder o suporte a Conda. A
leitura de `environment.yml` não degrada mais em silêncio para uma lista vazia — ou o
formato é lido, ou a instalação está incompleta.

### Ingestão apenas por upload

O [ADR-0001](./docs/adr/0001-ingestao-por-upload-e-por-diretorio.md) decide suportar
ingestão por upload **e** por diretório local. Hoje só o upload está implementado.

---

## Estrutura do Projeto

```
.
├── core/                            # Lógica principal — nada aqui importa streamlit
│   ├── ingestion/
│   │   ├── decompressor.py          # Leitura de .zip, .tar e .tar.gz em memória
│   │   ├── archive_walker.py        # Percorre o archive e lê os arquivos que interessam
│   │   └── filter.py                # Exclusões, validação do archive e pastas ignoradas
│   │
│   ├── parsin/
│   │   ├── readers.py               # Parsers registrados por arquivo (READERS)
│   │   ├── declaration_collector.py # Une todas as Declarações no conjunto auditado
│   │   ├── lock_resolver.py         # Resolve a Versão Usada a partir do Lock
│   │   ├── dependency_parser.py     # Normaliza e padroniza a lista de declaradas
│   │   └── import_parser.py         # Extrai Imports Raiz via AST
│   │
│   ├── analysis/
│   │   ├── zombie_analizer.py       # Declaradas de Produção não importadas
│   │   ├── ghost_analizer.py        # Imports Raiz não declarados
│   │   ├── outdated_analizer.py     # Compara Versão Usada com a versão do PyPI
│   │   └── name_matching.py         # Alias de Import: Distribuição ↔ Nome de Import
│   │
│   ├── pypi/
│   │   └── pypi_client.py           # API pública do PyPI: versão, Tamanho e Idade
│   │
│   └── report/
│       ├── normalization.py         # Estruturação final dos dados para exibição
│       ├── statistics.py            # Tamanho somado e Idade média por Categoria
│       └── export.py                # Exportação para CSV e JSON
│
├── pages/                           # Interface Streamlit
│   ├── home.py                      # Upload do Projeto-Alvo e escolha das Exclusões
│   ├── loading.py                   # Orquestra o pipeline com feedback por etapa
│   └── report.py                    # Relatório, métricas e gráficos
│
├── utils/
│   ├── constants.py                 # Cores, URL do PyPI, stdlib, IMPORT_ALIASES
│   ├── functions.py                 # Registries READERS e EXTRATORES (decorador)
│   └── sidebar.py                   # Sidebar reutilizável
│
├── tests/units/                     # Testes unitários espelhando core/, pages/ e utils/
│   ├── analysis/
│   ├── ingestion/
│   ├── pages/
│   ├── parsin/
│   ├── pypi/
│   ├── report/
│   └── utils/
│
├── docs/
│   ├── Enunciado.md                 # Requisitos e histórias de usuário
│   ├── adr/                         # Registros de decisão de arquitetura
│   └── grills_logs/                 # Logs das sessões de grill
│
├── CONTEXT.md                       # Glossário do domínio
├── main.py                          # Ponto de entrada — navegação Streamlit
├── pyproject.toml                   # Dependências do próprio ORÁCULO
└── uv.lock                          # Lock gerado pelo uv
```

---

## Pipeline de Análise

```
Arquivo .zip / .tar / .tar.gz
        │
        ▼
  decompressor.py          — abre o archive em memória (sem extrair para disco)
        │
        ▼
  filter.py                — valida o archive e aplica as Exclusões
        │
        ▼
  loading.py               — orquestra as etapas com feedback visual
        │
        ├──▶ declaration_collector.py → readers.py   — une as Declarações (o conjunto)
        │
        ├──▶ lock_resolver.py                        — Lock resolve a Versão Usada
        │
        ├──▶ import_parser.py                        — extrai Imports Raiz via AST
        │
        ├──▶ zombie_analizer.py / ghost_analizer.py  — cruza declaradas × importadas
        │
        └──▶ outdated_analizer.py + pypi_client.py   — PyPI: versão, Tamanho e Idade
                    │
                    ▼
              normalization.py → statistics.py   — consolida e estratifica por Categoria
                    │
                    ▼
              report.py → export.py              — exibe e exporta CSV / JSON
```

---

## Instalação e Execução

**Pré-requisitos:** Python 3.11+

### Com uv (recomendado)

```bash
uv sync                        # instalar dependências
uv run streamlit run main.py   # executar a aplicação
uv run pytest                  # rodar os testes
```

### Com pip

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
.venv\Scripts\activate          # Windows

pip install streamlit plotly requests packaging pyyaml
streamlit run main.py
```

---

## Dependências da Aplicação

| Pacote | Uso |
|---|---|
| `streamlit` | Interface web e navegação entre páginas |
| `plotly` | Gráficos do relatório |
| `requests` | Requisições à API do PyPI |
| `packaging` | Comparação semântica de versões no `outdated_analizer` |
| `pyyaml` | Leitura de `environment.yml` (Conda) no `readers` |

---

## Uso

1. Acesse `http://localhost:8501` após iniciar a aplicação.
2. Faça o upload do `.zip`, `.tar` ou `.tar.gz` do Projeto-Alvo.
3. Opcionalmente, marque as pastas que ficam de fora da auditoria (Exclusões — ex.:
   `tests`, `docs`).
4. Clique em **Executar Análise Completa** e acompanhe o progresso.
5. Leia o relatório: métricas gerais, tabelas por Categoria (Todas, Zumbis, Fantasmas,
   Desatualizadas), Tamanho e Idade estratificados, e os gráficos.
6. Exporte o resultado em CSV ou JSON.

> O próprio ORÁCULO é um Projeto-Alvo válido — auditá-lo é a forma mais rápida de testar.

---
