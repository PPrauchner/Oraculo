"""
Módulo de constantes para a aplicação.

Define valores fixos e configurações utilizadas em toda a aplicação,
como temas, cores, fontes e outros parâmetros de estilo.
"""

from core.parsin.normalization import list_all
from core.analysis.ghost_analizer import list_ghosts
from core.analysis.zombie_analizer import list_zombies
from core.analysis.outdated_analizer import list_outdated

# ============ Cores =================#

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

ARQUIVOS = [
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "target",
    ".git",
    ".svn",
    ".hg",
]
GERADORES = {
    "Todas as Dependências": list_all,
    "Zumbis": list_zombies,
    "Fantasmas": list_ghosts,
    "Desatualizadas": list_outdated,
}
