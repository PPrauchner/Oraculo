# Problema 01


📂 parsin/ (já refinado)
🔹 dependency_parser.py

Extrai dependências declaradas

Lê pyproject.toml e requirements.txt

Retorna:

nome

versão

🔹 import_parser.py

Varre código-fonte

Identifica imports usados

Respeita diretórios ignorados

🔹 normalization.py

Padroniza nomes

Resolve diferenças entre:

nome do pacote

nome do import

📂 ingestion/

Aqui começa o “poder” da ferramenta: dados externos.

🔹 filter.py
👉 Responsabilidade:

Filtrar e preparar dados antes da análise

📌 Ele deve:

Aplicar regras de exclusão:

diretórios ignorados

arquivos irrelevantes

Remover:

dependências padrão da linguagem (stdlib)

Garantir que só dados relevantes avancem

🔹 decompressor.py
👉 Responsabilidade:

Preparar o projeto para análise

📌 Ele deve:

Lidar com entradas como:

.zip

.tar.gz

Extrair conteúdo para análise

👉 Se teu projeto não recebe arquivos compactados, ele pode ser simplificado ou removido.

🔥 (IMPORTANTE – faltando conceitualmente)

Tu vai precisar de algo como:

🔹 pypi_client (mesmo que não esteja no projeto ainda)
👉 Responsabilidade:

Buscar dados no PyPI

📌 Ele deve:

Consultar:

versão mais recente

data de release

Retornar:

latest_version

release_date

histórico (se quiser evoluir)

📂 analysis/

Aqui acontece a lógica principal do problema.

🔹 ghost_analyzer.py
👉 Responsabilidade:

Detectar dependências fantasmas

📌 Regra:
import usado no código
MAS não está declarado
📌 Entrada:

imports usados

dependências declaradas

📌 Saída:

lista de fantasmas

🔹 zombie_analyzer.py
👉 Responsabilidade:

Detectar dependências zumbis

📌 Regra:
dependência declarada
MAS não é usada no código
📌 Entrada:

dependências declaradas

imports usados

📌 Saída:

lista de zumbis

🔹 outdated_analyzer.py
👉 Responsabilidade:

Detectar dependências desatualizadas

📌 Regra:
versão usada < versão mais recente no PyPI
📌 Entrada:

dependências declaradas

dados do PyPI

📌 Saída:

lista com:

versão atual

versão latest

diferença

📂 report/

Transforma dados técnicos em algo utilizável.

🔹 make_report.py
👉 Responsabilidade:

Construir o relatório estruturado

📌 Ele deve:

Consolidar:

todas dependências

zumbis

fantasmas

desatualizadas

Calcular:

quantidade

idade (data atual - release)

tamanho (se disponível)

📌 Saída:

estrutura pronta para GUI e exportação

🔹 csv_export.py
👉 Responsabilidade:

Exportar relatório

📌 Ele deve:

Gerar CSV com:

categorias separadas

dados organizados

Permitir histórico (salvar múltiplas execuções)

📂 gui/

Interface com o usuário.

🔹 home.py
👉 Responsabilidade:

Tela inicial

📌 Deve permitir:

Upload ou seleção do projeto

Configurar:

diretórios ignorados

Iniciar análise

🔹 report.py
👉 Responsabilidade:

Exibir resultados

📌 Deve mostrar:

métricas gerais

listas:

dependências

zumbis

fantasmas

desatualizadas

📌 Extras importantes:

botão de exportar CSV

visualização clara (tabelas/gráficos)

📄 main.py
👉 Responsabilidade:

Orquestração geral

📌 Ele deve:

Conectar tudo:

parsing

ingestion

analysis

report

gui

👉 É o “controlador” da aplicação