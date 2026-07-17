"""
Testes das constantes de estilo da aplicação.

Cobre o mapa de cores por status (MAPA_CORES_STATUS), cujas chaves precisam
casar exatamente com os rótulos que o gráfico de rosca usa em pages/report.py,
sem espaços parasitas.
"""

from utils.constants import MAPA_CORES_STATUS

# Rótulos que o gráfico de rosca realmente usa (pages/report.py):
# "OK ✅" (saudáveis) + os valores de CATEGORY_NAMES para as categorias problemáticas.
DONUT_STATUS_LABELS = {"OK ✅", "Zumbis", "Fantasmas", "Desatualizadas"}


def test_color_map_keys_match_donut_labels():
    """As chaves do mapa de cores casam exatamente com os rótulos do gráfico."""
    assert set(MAPA_CORES_STATUS.keys()) == DONUT_STATUS_LABELS


def test_color_map_keys_have_no_stray_whitespace():
    """Nenhuma chave tem espaço parasita à esquerda ou à direita."""
    for key in MAPA_CORES_STATUS:
        assert key == key.strip()
