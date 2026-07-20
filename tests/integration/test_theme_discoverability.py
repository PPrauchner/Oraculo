"""
Guarda a sinalização de que o tema claro/escuro existe e onde trocá-lo.

O ORÁCULO tem os dois modos desde a #39, e o menu nativo do Streamlit já alterna
entre eles por sessão. O que faltava não era capacidade, era **descoberta**: o menu
mora atrás de um ⋮ no canto, e quem não conhece Streamlit nunca o abre.

A sinalização é uma legenda, e não um controle, de propósito. `theme.base` é
`scriptable = False` — trocar o tema por código levantaria exceção, e contornar isso
pela API privada trocaria uma preferência por-sessão por uma global do servidor
(registro em `.out-of-scope/seletor-de-tema-customizado.md`). Uma dica que parece
botão e não alterna nada é pior do que não sinalizar.

Responsabilidades:
- Guardar que a dica aparece na barra lateral, em qualquer língua.
- Guardar que ela aponta o caminho do menu nativo.
- Guardar que ela não se apresenta como controle clicável.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from utils.i18n import available_languages, translate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_PAGE = str(PROJECT_ROOT / "pages" / "home.py")

# A chave única da dica. Um só rótulo: a sinalização compete com os controles reais
# da ferramenta se crescer além de uma linha.
THEME_HINT = "sidebar.theme_hint"


def _run(language: str) -> AppTest:
    """Abre a página inicial na língua pedida, como um navegador abriria."""
    app = AppTest.from_file(HOME_PAGE, default_timeout=30)
    app.query_params["lang"] = language

    return app.run()


@pytest.mark.parametrize("language", available_languages())
def test_the_sidebar_tells_the_visitor_the_theme_can_be_switched(language: str):
    """A dica é permanente: ela está lá na primeira renderização, sem precisar de clique.

    É o requisito inteiro da #48 — o mecanismo já existia e funcionava; o que não
    existia era qualquer coisa na tela dizendo que ele existe.
    """
    app = _run(language)

    captions = [caption.value for caption in app.sidebar.caption]

    assert translate(THEME_HINT, language) in captions


@pytest.mark.parametrize("language", available_languages())
def test_the_hint_names_the_path_to_the_native_menu(language: str):
    """Dizer que o tema existe sem dizer onde não resolve nada — o menu continua escondido.

    O caminho (`⋮ → Settings → Theme`) fica em inglês em toda língua porque é o rótulo
    que o Streamlit desenha: traduzi-lo mandaria o visitante procurar um item que não
    está na tela dele.
    """
    hint = translate(THEME_HINT, language)

    assert "⋮" in hint
    assert "Settings" in hint
    assert "Theme" in hint


# Elementos que o visitante clica esperando que algo aconteça.
CLICKABLE_ELEMENTS = ("button", "toggle", "checkbox", "radio", "selectbox", "multiselect")


@pytest.mark.parametrize("language", available_languages())
def test_the_hint_is_not_dressed_up_as_a_control(language: str):
    """Dica que parece botão e não alterna nada é pior do que dica nenhuma.

    O ORÁCULO não tem um alternador próprio para oferecer — `theme.base` não é
    scriptable. Então a sinalização precisa se parecer com o que é: uma legenda que
    aponta o caminho, e não um controle que promete alternar.
    """
    app = _run(language)
    hint = translate(THEME_HINT, language)

    labels = [
        element.label
        for kind in CLICKABLE_ELEMENTS
        for element in getattr(app.sidebar, kind, [])
        if isinstance(getattr(element, "label", None), str)
    ]

    assert hint not in labels
