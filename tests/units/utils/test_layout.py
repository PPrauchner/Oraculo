"""
Guarda do ponto único de layout da aplicação.

A #39 tirou das páginas o CSS que cravava aparência à mão. O ritmo vertical e a
largura de leitura, porém, o Streamlit não expõe de forma declarativa — então aqui
uma folha de estilo é inevitável. Estes testes são o que separa esta folha daquela
que foi removida: ela é única, é só layout e não se prende a atributo interno do
Streamlit. Sem eles, "CSS de layout num só lugar" seria promessa, e não propriedade.

Responsabilidades:
- Guardar que a folha é emitida uma vez, e só pelo ponto de entrada.
- Guardar que ela não carrega cor nem tipografia.
- Guardar que ela não se acopla a `data-testid`.
- Guardar que ela de fato aperta o respiro e limita a largura de leitura.
"""

import ast
import re
from pathlib import Path

import pytest
import streamlit as st

from utils.layout import LAYOUT_STYLESHEET, apply_layout

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENTRY_POINT = PROJECT_ROOT / "main.py"
PAGES_DIR = PROJECT_ROOT / "pages"


def _apply_layout_calls(source: str) -> int:
    """Quantas vezes o módulo chama `apply_layout()`."""
    tree = ast.parse(source)

    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "apply_layout"
    )


# Espaço que o Streamlit reserva acima do primeiro elemento quando ninguém manda o
# contrário. É o número que esta issue existe para baixar.
STREAMLIT_DEFAULT_TOP_PADDING_REM = 6.0


def _declarations(stylesheet: str) -> dict[str, str]:
    """Propriedades CSS declaradas na folha, mapeadas no valor."""
    return {
        prop.strip(): value.strip()
        for prop, value in re.findall(r"([\w-]+)\s*:\s*([^;{}]+);", stylesheet)
    }


def _rem(value: str) -> float:
    """Converte um comprimento em `rem` no número que ele vale."""
    return float(value.removesuffix("rem"))


def _emitted_html(monkeypatch) -> list[str]:
    """Captura o que `apply_layout()` manda para a tela."""
    emitted: list[str] = []
    monkeypatch.setattr(st, "html", emitted.append)
    apply_layout()

    return emitted


def test_apply_layout_emits_a_single_stylesheet(monkeypatch):
    """Uma chamada, uma folha — não um bloco por seção da tela."""
    emitted = _emitted_html(monkeypatch)

    assert len(emitted) == 1
    assert emitted[0].count("<style") == 1


def test_the_entry_point_applies_the_layout_once():
    """`main.py` roda antes de qualquer página, então uma chamada cobre a aplicação."""
    assert _apply_layout_calls(ENTRY_POINT.read_text(encoding="utf-8")) == 1


@pytest.mark.parametrize(
    "module", sorted(PAGES_DIR.glob("*.py")), ids=lambda path: path.name
)
def test_no_page_applies_the_layout_on_its_own(module: Path):
    """Nenhuma página reaplica o layout.

    Ponto único é o que separa esta folha da que a #39 removeu: uma chamada por
    página traria de volta o CSS espalhado, só que com outro nome.
    """
    assert _apply_layout_calls(module.read_text(encoding="utf-8")) == 0


def test_the_layout_tightens_the_vertical_rhythm():
    """O respiro do topo encolhe: os controles cabem na primeira dobra do notebook."""
    top_padding = _declarations(LAYOUT_STYLESHEET)["padding-top"]

    assert _rem(top_padding) < STREAMLIT_DEFAULT_TOP_PADDING_REM


def test_the_layout_caps_the_reading_width():
    """A leitura tem teto: num ultrawide a página para de se espalhar.

    Um teto em pixels, e não em porcentagem — `max-width: 90%` volta a crescer com o
    monitor, que é exatamente o que a issue #50 reclama.
    """
    reading_width = _declarations(LAYOUT_STYLESHEET)["max-width"]

    assert reading_width.endswith("px")
    assert float(reading_width.removesuffix("px")) > 0


def test_the_layout_declares_no_appearance():
    """A folha é só layout: nenhuma propriedade de cor, fundo ou tipografia.

    Era isto que a `visual_css()` da #39 fazia de errado — cravar um azul só dela,
    fora do alcance do tema. Cor, fundo e borda continuam saindo inteiros de
    `.streamlit/config.toml`, e uma folha de layout não tem o que opinar sobre eles.
    """
    appearance = {
        prop
        for prop in _declarations(LAYOUT_STYLESHEET)
        if "color" in prop or "background" in prop or "font" in prop
    }

    assert appearance == set()


def test_the_layout_writes_no_literal_color():
    """Nenhum hex, `rgb()` ou `hsl()` solto na folha."""
    literal_colors = re.findall(
        r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\s*\(", LAYOUT_STYLESHEET
    )

    assert literal_colors == []


def test_the_layout_binds_to_no_internal_test_attribute():
    """O seletor não se prende a `data-testid`, que é detalhe interno do Streamlit.

    `data-testid` é contrato de teste da ferramenta, não API pública: ele muda de
    versão para versão e levaria o layout junto, em silêncio. `.block-container` é
    classe pública e sobrevive ao upgrade.
    """
    assert "data-testid" not in LAYOUT_STYLESHEET
