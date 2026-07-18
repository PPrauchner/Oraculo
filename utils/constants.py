"""
Módulo de constantes para a aplicação.

Define valores fixos e configurações utilizadas em toda a aplicação,
como temas, cores, fontes e outros parâmetros de estilo.
"""

# ============ Cores =================#

import sys


MAPA_CORES_STATUS = {
    "OK ✅": "#2ECC71",  # GREEN
    "Zumbis": "#9B59B6",  # PURPLE
    "Fantasmas": "#E74C3C",  # RED
    "Desatualizadas": "#3498DB",  # BLUE
}
COR_PADRAO = "#95A5A6"
BLUE = "#3498DB"
GREEN = "#2ECC71"
RED = "#E74C3C"
PURPLE = "#9B59B6"
# ============ Cores =================#

SVG_LUPA = """
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" transform="scale(-1, 1)" transform-origin="center" style="margin-right: 10px; vertical-align: middle; color: #4F8BF9;">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    </svg>
    """

PYPI_BASE_URL = "https://pypi.org/pypi"

# ============ Origem =================#
# De qual Declaração — e de qual seção dela — um pacote veio. Separa Dependência
# de Produção de Dependência de Desenvolvimento (ver CONTEXT.md e ADR-0003).

ORIGIN_PRODUCTION = "Produção"
ORIGIN_DEVELOPMENT = "Desenvolvimento"
# ============ Origem =================#

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
# de Import que o pacote expõe. Sem isso, um mesmo pacote vira Fantasma e Zumbi ao
# mesmo tempo (ex.: PyYAML ↔ yaml). Ver CONTEXT.md (Alias de Import) e a limitação
# documentada no README: pacotes fora desta tabela ainda geram o par de falsos
# positivos. Um pacote pode expor mais de um Nome de Import (ex.: setuptools).
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
    "protobuf": ["google"],  # protobuf
    "pycryptodome": ["Crypto"],  # pycryptodome
    "setuptools": ["setuptools", "pkg_resources"],  # múltiplos Nomes de Import
    "attrs": ["attr", "attrs"],  # múltiplos Nomes de Import
}
# ============ Alias de Import =================#
