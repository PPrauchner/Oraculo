# DP-Auditor — Auditoria de Dependências Python

Ferramenta web para análise de dependências de projetos Python. Detecta dependências **zumbis**, **fantasmas** e **desatualizadas** a partir do upload de um arquivo compactado do projeto.

---

## Funcionalidades

- **Zumbis** — dependências declaradas nos arquivos de configuração mas não importadas no código-fonte
- **Fantasmas** — imports usados no código-fonte mas não declarados em nenhum arquivo de configuração
- **Desatualizadas** — dependências com versão inferior à disponível no PyPI
- **Índice de Saúde** — métrica geral do estado das dependências do projeto
- **Exportação** — relatório exportável em CSV e JSON
- **Paralelismo** — consultas ao PyPI feitas em paralelo para reduzir o tempo de análise

---

## Formatos de Configuração Suportados

| Arquivo | Gerenciador |
|---|---|
| `requirements.txt` | pip |
| `environment.yml` | Conda |
| `*.lock` | uv, Poetry |

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

---

## Estrutura do Projeto

```
problema-01/
│
├── core/                          # Lógica principal da aplicação
│   ├── ingestion/
│   │   ├── decompressor.py        # Leitura de .zip, .tar e .tar.gz em memória
│   │   └── filter.py              # Filtro de caminhos, pastas ignoradas e validação do archive
│   │
│   ├── parsin/
│   │   ├── readers.py             # Parsers registrados: requirements.txt, environment.yml, *.lock
│   │   ├── dependency_parser.py   # Normaliza e padroniza a lista de dependências declaradas
│   │   └── import_parser.py       # Extrai imports externos via AST
│   │
│   ├── analysis/
│   │   ├── zombie_analizer.py     # Detecta dependências declaradas não importadas
│   │   ├── ghost_analizer.py      # Detecta imports não declarados
│   │   └── outdated_analizer.py   # Consulta PyPI em paralelo e classifica versões
│   │
│   ├── pypi/
│   │   └── pypi_client.py         # Requisições à API REST do PyPI
│   │
│   └── report/
│       ├── export.py              # Exportação para CSV e JSON
│       └── normalization.py       # Estruturação final dos dados para exibição
│
├── pages/                         # Páginas da interface Streamlit
│   ├── home.py                    # Tela inicial — upload do arquivo e configuração de exclusões
│   ├── loading.py                 # Orquestração do pipeline com feedback visual por etapas
│   └── report.py                  # Exibição do relatório, métricas e gráfico de proporção
│
├── utils/                         # Utilitários compartilhados entre módulos
│   ├── constants.py               # Cores, URL do PyPI, stdlib e constantes globais
│   ├── functions.py               # Dicionários READERS e EXTRATORES com sistema de registro via decorador
│   └── sidebar.py                 # Componente de sidebar reutilizável
│
├── tests/                         # Testes unitários
│   └── units/
│       ├── analysis/
│       │   ├── test_ghosts.py
│       │   ├── test_outdated.py
│       │   └── test_zombies.py
│       ├── ingestion/
│       │   └── test_decompressor.py
│       ├── parsin/
│       │   └── test_import_parser.py
│       └── report/
│           ├── test_export.py
│           └── test_normalization.py
│
├── main.py                        # Ponto de entrada — configura navegação entre páginas Streamlit
├── pyproject.toml                 # Dependências do próprio projeto DP-Auditor
└── uv.lock                        # Lock file gerado pelo uv
```

---

## Pipeline de Análise

```
Arquivo .zip / .tar / .tar.gz
        │
        ▼
  decompressor.py          — abre o arquivo em memória (sem extração para disco)
        │
        ▼
  filter.py                — valida se o archive contém .py e arquivo de dependências
        │
        ▼
  loading.py               — orquestra as etapas com feedback visual
        │
        ├──▶ readers.py → dependency_parser.py   — lê requirements.txt / environment.yml / *.lock
        │
        ├──▶ import_parser.py                    — extrai imports externos via AST
        │
        ├──▶ zombie_analizer.py                  — deps declaradas não importadas
        │
        ├──▶ ghost_analizer.py                   — imports não declarados
        │
        └──▶ outdated_analizer.py + pypi_client  — consulta PyPI em paralelo
                    │
                    ▼
              report.py    — exibe métricas, tabelas por categoria e gráfico de proporção
                    │
                    ▼
              export.py    — exporta CSV / JSON sob demanda
```

---

## Instalação e Execução

**Pré-requisitos:** Python 3.11+

### Com uv (recomendado)

```bash
# Instalar dependências
uv sync

# Executar a aplicação
uv run streamlit run main.py
```

### Com pip

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
.venv\Scripts\activate          # Windows

# Instalar dependências
pip install streamlit plotly pandas altair packaging

# Executar a aplicação
streamlit run main.py
```

---

## Dependências da Aplicação

| Pacote | Uso |
|---|---|
| `streamlit` | Interface web e navegação entre páginas |
| `plotly` | Gráfico de proporção de problemas |
| `pandas` | Manipulação de tabelas |
| `altair` | Visualizações auxiliares |
| `packaging` | Comparação semântica de versões no outdated_analizer |

---

## Uso

1. Acesse `http://localhost:8501` após iniciar a aplicação
2. Na tela inicial, faça o upload do arquivo `.zip`, `.tar` ou `.tar.gz` do projeto a ser analisado
3. Opcionalmente, selecione pastas a ignorar na análise (ex: `tests`, `docs`)
4. Clique em **Executar Análise Completa** e aguarde — o progresso é exibido em tempo real
5. Visualize o relatório com métricas gerais, tabelas por categoria (Todas, Zumbis, Fantasmas, Desatualizadas) e gráfico de proporção
6. Exporte o resultado em CSV ou JSON pelo botão na tela de relatório

---