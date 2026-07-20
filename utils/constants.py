"""
Módulo de constantes para a aplicação.

Define valores fixos e configurações utilizadas em toda a aplicação,
como temas, cores, fontes e outros parâmetros de estilo.
"""

# ============ Cores =================#
# Nenhuma cor é definida aqui. A paleta é única e mora em `.streamlit/config.toml`;
# este módulo só diz *qual token* cada Categoria usa, e `utils/theme.py` resolve o
# token na cor. Guardar o hex nos dois lugares é o que fazia a paleta divergir —
# eram três azuis diferentes antes (issue #39).

import sys


# Categoria (identidade estável, como `pages/report.py` a nomeia) -> token semântico
# do tema. O Streamlit já adapta esses tokens aos dois fundos, então a Categoria não
# precisa saber se a tela está clara ou escura.
#
# A chave é a identidade, não o rótulo: o rótulo muda com a língua (ADR-0009) e a
# cor de uma Categoria não pode depender do idioma em que a tela está aberta.
STATUS_COLOR_TOKENS = {
    "healthy": "greenColor",  # Saudável
    "zombies": "violetColor",
    "ghosts": "redColor",
    "outdated": "blueColor",
}
# ============ Cores =================#

# A lupa herda a cor de quem a contém (`stroke="currentColor"`), então ela segue o
# tema sem carregar cor própria.
SVG_LUPA = """
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" transform="scale(-1, 1)" transform-origin="center" style="margin-right: 10px; vertical-align: middle;">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    </svg>
    """

PYPI_BASE_URL = "https://pypi.org/pypi"

# ============ Origem =================#
# De qual Declaração — e de qual seção dela — um pacote veio. Separa Dependência
# de Produção de Dependência de Desenvolvimento (ver CONTEXT.md e ADR-0003).

ORIGIN_PRODUCTION = "Production"
ORIGIN_DEVELOPMENT = "Development"
# Fantasma não vem de Declaração, logo não tem Origem: é assim que ele se identifica
# no relatório e na exportação (ver `is_ghost`).
ORIGIN_UNAVAILABLE = "N/A"
# ============ Origem =================#

# ============ Categoria =================#
# Classificação de uma dependência no relatório/exportação. Derivada das listas de
# análise (Zumbi, Fantasma) — o restante auditado é Saudável. Desatualizada NÃO é
# Categoria: é coluna própria, pois uma dependência pode ser Zumbi e Desatualizada ao
# mesmo tempo (ver CONTEXT.md e a issue US-06/US-07).
CATEGORY_ZOMBIE = "Zombie"
CATEGORY_GHOST = "Ghost"
CATEGORY_HEALTHY = "Healthy"

# Marca da coluna Desatualizada na exportação (booleano legível).
OUTDATED_YES = "Yes"
OUTDATED_NO = "No"
# ============ Categoria =================#

# ============ Lock =================#
# Extensão dos arquivos de Lock (uv.lock, poetry.lock). O Lock resolve versões,
# não define o conjunto auditado (ADR-0002).
LOCK_EXTENSION = ".lock"
# ============ Lock =================#

# ============ Versão Usada =================#
# Valor reportado quando a Versão Usada é indisponível: sem Lock e sem pin, não se
# conhece a versão que o Projeto-Alvo executa, então Idade/Tamanho ficam indefinidos
# (ADR-0002). Nunca assumir a versão do PyPI nesse caso.
VERSION_UNAVAILABLE = "N/D"
# ============ Versão Usada =================#

PYTHON_STDLIB_MODULES = getattr(sys, "stdlib_module_names", set())

# ============ Alias de Import =================#
# Mapeia Nome de Distribuição (normalizado: minúsculas e "-" -> "_") para os Nomes
# de Import que o pacote expõe *além do próprio nome* — `import_names_for` já
# acrescenta o nome normalizado, então repeti-lo aqui é redundante. Sem esta tabela um
# mesmo pacote vira Fantasma e Zumbi ao mesmo tempo (ex.: PyYAML ↔ yaml). Ver
# CONTEXT.md (Alias de Import) e a limitação documentada no README: pacotes fora desta
# tabela ainda geram o par de falsos positivos.
#
# Namespace compartilhado não entra: mapear `protobuf` para `google` faria um projeto
# que importa `google.cloud.storage` "usar" um protobuf declarado e ocioso — falso
# negativo na US-03, o inverso do que a tabela resolve.
IMPORT_ALIASES: dict[str, list[str]] = {
    "pyyaml": ["yaml"],  # PyYAML
    "scikit_learn": ["sklearn"],  # scikit-learn
    "opencv_python": ["cv2"],  # opencv-python
    "opencv_python_headless": ["cv2"],  # opencv-python-headless
    "pillow": ["PIL"],  # Pillow
    "beautifulsoup4": ["bs4"],  # beautifulsoup4
    "python_dateutil": ["dateutil"],  # python-dateutil
    "python_dotenv": ["dotenv"],  # python-dotenv
    "python_docx": ["docx"],  # python-docx
    "python_pptx": ["pptx"],  # python-pptx
    "pycryptodome": ["Crypto"],  # pycryptodome
    "setuptools": ["pkg_resources"],  # expõe mais de um Nome de Import
    "attrs": ["attr"],  # expõe mais de um Nome de Import
}
# ============ Alias de Import =================#
