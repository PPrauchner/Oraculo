"""
Testes das constantes de estilo da aplicação.

Cobre o mapa de tokens por status (STATUS_COLOR_TOKENS), cujas chaves precisam
casar exatamente com os rótulos que o gráfico de rosca usa em pages/report.py,
sem espaços parasitas, e cujos valores são tokens semânticos do tema — não hexes.
"""

import re
from pathlib import Path

from utils.constants import STATUS_COLOR_TOKENS

# Rótulos que o gráfico de rosca realmente usa (pages/report.py):
# "OK ✅" (saudáveis) + os valores de CATEGORY_NAMES para as categorias problemáticas.
DONUT_STATUS_LABELS = {"OK ✅", "Zumbis", "Fantasmas", "Desatualizadas"}


def test_color_map_keys_match_donut_labels():
    """As chaves do mapa de tokens casam exatamente com os rótulos do gráfico."""
    assert set(STATUS_COLOR_TOKENS.keys()) == DONUT_STATUS_LABELS


def test_color_map_keys_have_no_stray_whitespace():
    """Nenhuma chave tem espaço parasita à esquerda ou à direita."""
    for key in STATUS_COLOR_TOKENS:
        assert key == key.strip()


def test_categorias_apontam_para_tokens_semanticos_nao_para_hexes():
    """Cada Categoria carrega o nome de um token do tema, não uma cor fixa.

    Guardar o hex aqui é o que fazia a paleta existir em dois lugares e divergir.
    O valor certo é o nome do token; quem resolve a cor é `utils/theme.py`.
    """
    for label, token in STATUS_COLOR_TOKENS.items():
        assert not token.startswith("#"), f"{label} guarda um hex, não um token"
        assert token.endswith("Color"), f"{label} não aponta para um token do tema"


def test_constantes_nao_carregam_cor_fixa():
    """Nenhum hex sobrou no módulo: a paleta mora só no config.toml."""
    import utils.constants as constants

    source = Path(constants.__file__).read_text(encoding="utf-8")

    assert re.findall(r"#[0-9A-Fa-f]{6}\b", source) == []
