# 🔍 Dependency Analyzer Tool

## 📌 Descrição

Ferramenta para análise de dependências em projetos Python.

A aplicação recebe um projeto compactado em `.zip`, analisa seus arquivos de configuração e código-fonte, e gera um relatório detalhado sobre o uso e o estado das dependências.

---

## 🎯 Objetivo

A ferramenta tem como objetivo:

* Analisar arquivos de dependências:

  * `pyproject.toml`
  * `requirements.txt`
* Analisar o código-fonte (`.py`)
* Cruzar as informações para identificar:

### 🧟 Dependências zumbis

Dependências declaradas, mas não utilizadas no código.

### 👻 Dependências fantasmas

Dependências utilizadas no código, mas não declaradas.

### ⏳ Dependências desatualizadas

Dependências com versão inferior à disponível no PyPI.

---

## 🌐 Consulta ao PyPI

A verificação de versões é realizada utilizando a API pública:

```
https://pypi.org/pypi/<nome-do-pacote>/json
```

---

## ⚙️ Funcionalidades

### 📊 Relatório completo

A ferramenta gera um relatório contendo:

#### 🔹 Total de dependências

* Lista de dependências
* Quantidade
* Tamanho
* Idade (data atual - data de lançamento da versão)

#### 🔹 Dependências zumbis

* Lista
* Quantidade
* Tamanho
* Idade

#### 🔹 Dependências fantasmas

* Lista
* Quantidade
* Tamanho
* Idade

---

### 💾 Exportação

* Visualização via interface gráfica
* Exportação em formato **CSV**

---

### ⚙️ Configuração

O usuário pode:

* Definir o diretório raiz
* Ignorar diretórios (ex: `tests/`, `docs/`)

---

## 🧱 Arquitetura do Projeto

### 📁 Estrutura de Pastas

```
Projeto
│
├── core
│   └── analysis
│       ├── ghost_analyzer.py
│       ├── outdated_analyzer.py
│       └── zombie_analyzer.py
│
├── ingestion
│   ├── decompressor.py
│   └── filter.py
│
├── parsin
│   ├── dependency_parser.py
│   ├── import_parser.py
│   └── normalization.py
│
├── pypi
│   └── pypi_client.py
│
├── report
│   ├── make_report.py
│   └── csv_export.py
│
├── gui
│   ├── pages
│   │   ├── report.py
│   │   └── loading.py
│   │
│   ├── utils
│   │   └── sidebar.py
│   │
│   └── home.py
│
├── main.py
├── pyproject.toml
├── README.md
├── .python-version
└── .gitkeep
```

---

### 🧠 Organização por responsabilidade

```
Projeto
│
├── ingestion   → entrada de dados (ZIP, arquivos)
├── parsin      → interpretação (imports e dependências)
├── core        → regras de negócio (análises)
├── pypi        → integração externa (consulta de versões)
├── report      → geração e exportação de relatórios
├── gui         → interface gráfica (Streamlit)
│
└── main.py     → orquestra todo o fluxo da aplicação
```

---

## 🔄 Fluxo de Execução

1. Upload do projeto (`.zip`)
2. Leitura dos arquivos
3. Filtragem de arquivos relevantes
4. Parsing:

   * Dependências declaradas
   * Imports utilizados
5. Análise:

   * Dependências zumbis
   * Dependências fantasmas
   * Dependências desatualizadas
6. Consulta ao PyPI
7. Geração do relatório
8. Exibição e exportação

---

## ⚠️ Requisitos

* Python
* Paradigma de programação procedural
* Arquitetura modular
* Uso da API pública do PyPI
* Interface gráfica para interação do usuário

---

## 🚀 Possíveis Evoluções

* Exportação para Excel
* Histórico de análises
* Integração com CI/CD
* Análise incremental de dependências
* Suporte a múltiplos projetos

---
