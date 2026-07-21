"""
Testes das constantes de estilo da aplicação.

Cobre o mapa de tokens por status (STATUS_COLOR_TOKENS), cujas chaves precisam
casar exatamente com as categorias que o gráfico de rosca usa em pages/report.py,
sem espaços parasitas, e cujos valores são tokens semânticos do tema — não hexes.
"""

import re
from pathlib import Path

import pytest

from utils.constants import STATUS_COLOR_TOKENS
from utils.i18n import available_languages, load_locale

# Categorias que o gráfico de rosca realmente desenha (pages/report.py): "healthy"
# (as sem problema apontado) mais as três categorias problemáticas. São identidades
# estáveis, não rótulos — o rótulo muda com a língua e a cor não pode mudar junto.
DONUT_CATEGORIES = {"healthy", "zombies", "ghosts", "outdated"}


def test_color_map_keys_match_donut_categories():
    """As chaves do mapa de tokens casam exatamente com as categorias do gráfico."""
    assert set(STATUS_COLOR_TOKENS.keys()) == DONUT_CATEGORIES


@pytest.mark.parametrize("language", available_languages())
def test_every_colored_category_has_a_label_to_show(language: str):
    """A categoria colorida no donut tem rótulo em toda língua.

    A chave do mapa é a identidade, e é o rótulo que o Plotly casa com a cor: uma
    categoria sem entrada no locale desenharia a fatia com o identificador cru.
    """
    labels = load_locale(language)

    for category in STATUS_COLOR_TOKENS:
        assert f"report.category.{category}" in labels


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
