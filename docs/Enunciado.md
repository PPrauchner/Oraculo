*[English version](Enunciado.en.md)*

Projetos Python acumulam dependências ao longo do tempo, e é comum que bibliotecas fiquem desatualizadas, sem uso ou com vulnerabilidades conhecidas.

O objetivo deste projeto é desenvolver uma ferramenta que:
1. Analise arquivos de configuração de dependências (pyproject.toml ou requirements.txt) e o código-fonte do projeto.
2. Cruze as dependências declaradas com os imports reais encontrados no código-fonte.
3. Identifique três situações:
    a) Dependências declaradas mas não utilizadas no código (dependências "zumbis").
    b) Imports usados no código mas não declarados como dependências (dependências "fantasmas").
    c) Dependências com versões desatualizadas.

A checagem de versões deve ser feita consultando o repositório PyPI para verificar a versão mais recente disponível. O sistema deve permitir que o usuário configure arquivos e diretórios a serem ignorados (e.g., tests/, docs/), de modo que a análise foque somente no código principal do projeto-alvo.

A ferramenta deve:

1. Gerar um relatório estruturado, em interface gráfica, que indique:
    a) Total de dependências
        - Lista de dependências
        - Quantidade
        - Tamanho
        - Idade (data atual - data de lançamento da versão usada)
    b) Dependências zumbis
        - Lista de dependências
        - Quantidade
        - Tamanho
        - Idade (data atual - data de lançamento da versão usada)
    c) Dependências fantasmas
        - Lista de dependências
        - Quantidade
        - Tamanho
        - Idade (data atual - data de lançamento da versão usada)

2. Permitir exportar um relatório para acompanhamento ao longo do tempo. O relatório deve:
    a) Ser visualizável em interface gráfica
    b) Ser exportável em CSV

Histórias de Usuário
01. Como desenvolvedor, quero selecionar um projeto Python apontando para o diretório do código, para que a ferramenta analise as dependências e os imports.
02. Como desenvolvedor, quero que a ferramenta ignore arquivos e diretórios configurados (e.g., tests/, docs/), para focar na análise do código principal.
03. Como desenvolvedor, que a ferramenta cruze as dependências declaradas com os imports encontrados no código, para identificar dependências que são declaradas mas não usadas (dependências zumbis).
04. Como desenvolvedor, quero que a ferramenta identifique imports usados no código mas não declarados como dependências, para evitar falhas em outros ambientes (dependências fantasmas).
05. Como desenvolvedor, quero que a ferramenta consulte uma fonte de dados externa (i.e., PyPI) para verificar se as dependências usadas no projeto estão desatualizadas, para avaliar a necessidade de atualizações.
06. Como desenvolvedor, quero visualizar um relatório estruturado em interface gráfica com indicadores sobre as dependências para entender rapidamente a saúde do projeto. Quero que o relatório inclua, no mínimo, estatísticas do número de dependências, tamanho e idade das dependências, com informações estratificadas por categoria (total, zumbis, fantasmas, desatualizadas).
07. Como desenvolvedor, quero exportar o relatório das dependências do projeto em formato CSV, para acompanhar a evolução ao longo do tempo e realizar análises complementares.

Regras de Implementação
01. O projeto deve ser implementado em Python, utilizando o paradigma de programação procedural.
02. A análise de dependências deve ser feita através da varredura dos arquivos de configuração (e.g., pyproject.toml e requirements.txt) e do código-fonte (arquivos .py) do projeto.
03. A consulta de versões de dependências deve ser feita utilizando a API pública do PyPI (https://pypi.org/pypi/NOME_DA_DEPENDENCIA/json).
04. A configuração do projeto (diretório raiz, exclusões) deve ser feita através de interface gráfica.
05. O projeto deve ser implementado de forma modular, com funções e módulos separados de acordo com as responsabilidades de cada parte do sistema.

Dicas de Implementação
01. Utilize ferramentas como uv (https://uv.pypa.io/) ou Poetry (https://python-poetry.org/) para gestão de ambiente virtual e dependências do sistema.
02. Explore bibliotecas do Python como Streamlit (http://streamlit.io/) e Gradio (https://gradio.app/) para criar a interface gráfica.
03. Use módulos de leitura de arquivos ou manipulação de código nativos do Python para gerenciar o código-fonte do projeto de entrada cujas dependências serão analisadas.

Conceitos-Chave
01. Dependências de software.
02. Gerenciamento de ambientes virtuais e dependências.
03. Definição de interfaces gráficas.
04. Manipulação de arquivos.
05. Consumo de APIs externas.
06. Modularização de código.