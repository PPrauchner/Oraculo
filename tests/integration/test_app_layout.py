"""
O ponto único de layout exercitado pela aplicação de verdade, e não só pelo código.

Os testes de `tests/units/utils/test_layout.py` leem o módulo: provam que a folha é
única, é só layout e não se prende a `data-testid`. O que eles não alcançam é a
composição — se o ponto de entrada de fato aplica a folha, uma vez só, com o
`set_page_config` já resolvido antes. `AppTest` roda `main.py` como um navegador
rodaria, então é aqui que "existe um único ponto de layout" deixa de ser leitura de
código e vira propriedade observada.

Responsabilidades:
- Guardar que abrir a aplicação emite exatamente uma folha de estilo.
- Guardar que essa folha é a de layout, e que ela não carrega aparência.
- Guardar a hierarquia título → subtítulo → seções na tela inicial.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from utils.layout import LAYOUT_STYLESHEET

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENTRY_POINT = str(PROJECT_ROOT / "main.py")


@pytest.fixture
def app() -> AppTest:
    """A aplicação aberta pelo ponto de entrada, na página inicial."""
    running = AppTest.from_file(ENTRY_POINT, default_timeout=60).run()

    assert running.exception == []
    return running


def test_opening_the_app_emits_the_layout_stylesheet_once(app: AppTest):
    """Uma folha, emitida pelo ponto de entrada — e nenhuma segunda vinda da página.

    A tela inicial não declara estilo próprio (issue #39), então tudo o que sai daqui
    é a folha de layout. Uma segunda folha nesta contagem significa CSS voltando a
    nascer por página.
    """
    emitted = [element.body for element in app.get("html")]

    assert emitted == [LAYOUT_STYLESHEET]


def test_the_home_title_sits_above_the_section_headings(app: AppTest):
    """A hierarquia existe na tela: o maior nível ficou vazio e o título desceu um degrau.

    Com `st.title`, o título em tela larga achatava as seções logo abaixo. O que se
    afere aqui é a relação — nada no nível de cima, o título no nível médio e as duas
    seções um degrau abaixo dele.
    """
    assert [element.value for element in app.title] == []
    assert len(app.header) == 1
    assert len(app.subheader) == 2


def test_the_home_subtitle_is_rendered_as_a_caption(app: AppTest):
    """A linha de apoio sai como legenda: peso e cor secundários vindos do tema."""
    intro = app.caption[0].value

    assert "Target Project" in intro
