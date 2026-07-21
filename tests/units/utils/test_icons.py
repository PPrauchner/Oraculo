r"""
Guarda que os SVGs inline de `utils/icons.py` continuam sendo SVGs utilizaveis.

O `SVG_LUPA` tem dois papeis: decoracao do titulo da sidebar e favicon da aba. O favicon
depende de um detalhe fragil -- a deteccao de SVG inline do Streamlit so tolera um unico
espaco antes de `<svg` (`^\s?<svg`), entao um newline de indentacao no comeco da constante
manda `page_icon` para o ramo de arquivo e a aba fica sem icone (issue #45). Este teste
reproduz a conversao real do Streamlit para que essa regressao volte a falhar.

Responsabilidades:
- Garantir que `SVG_LUPA` vira um data URI de favicon, nao a string crua.
- Garantir que cada icone comeca em `<svg`, flush com as aspas.
"""

import pytest
from streamlit.commands.page_config import _get_favicon_string

from utils.icons import SVG_CHECK, SVG_LUPA


def test_lupa_becomes_a_favicon_data_uri():
    """O `page_icon` da aba: Streamlit rasteriza a lupa como data URI, nao a string crua."""
    favicon = _get_favicon_string(SVG_LUPA)

    assert favicon.startswith("data:image/svg+xml;base64,")


@pytest.mark.parametrize("svg", [SVG_LUPA, SVG_CHECK], ids=["lupa", "check"])
def test_icons_start_flush_with_svg(svg: str):
    """Sem whitespace inicial: e o que a deteccao de favicon exige e mantem a raiz coberta."""
    assert svg.startswith("<svg")
