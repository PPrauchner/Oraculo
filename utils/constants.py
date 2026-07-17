"""
Módulo de constantes para a aplicação.

Define valores fixos e configurações utilizadas em toda a aplicação,
como temas, cores, fontes e outros parâmetros de estilo.
"""

# ============ Cores =================#

import sys


MAPA_CORES_STATUS = {
    " OK ✅": "#2ECC71",  # GREEN
    " Zumbis 🧟": "#9B59B6",  # PURPLE
    " Fantasmas  ghosts 👻": "#E74C3C",  # RED
    " Desatualizadas ⏳": "#3498DB",  # BLUE
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

PYTHON_STDLIB_MODULES = getattr(sys, "stdlib_module_names", set())
