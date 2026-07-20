"""
A escolha de língua exercitada pela tela, e não só pela função que traduz.

O que o ADR-0009 promete só existe de verdade no runtime do Streamlit: abrir em
inglês, trocar pelo seletor, sobreviver ao refresh em `?lang=`. `AppTest` roda a
página de verdade — e vem dentro do próprio Streamlit, então provar isto não custa
nenhuma dependência nova.

Responsabilidades:
- Guardar o padrão inglês e o efeito do seletor sobre a URL.
- Guardar que nenhum rótulo traduzido encosta em `session_state`.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from utils.i18n import available_languages, load_locale, translate

HOME_PAGE = str(Path(__file__).resolve().parents[2] / "pages" / "home.py")


def _run(lang: str | None = None) -> AppTest:
    """Abre a página inicial como um navegador abriria, com ou sem `?lang=`.

    Args:
        lang: Valor de `?lang=` na URL. `None` para uma URL sem o parâmetro.

    Returns:
        A aplicação já executada.
    """
    app = AppTest.from_file(HOME_PAGE, default_timeout=30)

    if lang is not None:
        app.query_params["lang"] = lang

    return app.run()


def test_the_app_opens_in_english_without_a_lang_in_the_url():
    """Padrão inglês: o projeto virou portfólio e a banca deixou de ser o público."""
    app = _run()

    assert app.title[0].value == translate("home.title", "en")


def test_a_shared_link_arrives_already_translated():
    """`?lang=pt` na URL é o que faz o link ser compartilhável e sobreviver ao refresh."""
    app = _run("pt")

    assert app.title[0].value == translate("home.title", "pt")
    assert app.sidebar.markdown[1].value == translate("sidebar.subtitle", "pt")


def test_a_typed_garbage_lang_still_opens_the_app():
    """A URL é digitável: `?lang=klingon` abre em inglês em vez de derrubar a tela."""
    app = _run("klingon")

    assert app.exception == []
    assert app.title[0].value == translate("home.title", "en")


def test_the_selector_offers_every_language_in_its_own_name():
    """Cada opção no próprio idioma — o rótulo vem do arquivo, não de um mapa no código."""
    selector = _run().sidebar.selectbox[0]

    assert selector.options == [
        translate("language.name", language) for language in available_languages()
    ]


def test_choosing_a_language_writes_it_to_the_url():
    """O seletor não guarda a escolha em `session_state`: ele reescreve a URL.

    O `AppTest` devolve o parâmetro como lista, que é a forma crua do query string;
    o `st.query_params` da aplicação entrega o valor único.
    """
    app = _run()

    app.sidebar.selectbox[0].set_value("pt").run()

    assert app.query_params["lang"] == ["pt"]


def test_choosing_a_language_retranslates_the_screen():
    """Traduzir na renderização é o que evita rótulo velho até reexecutar a análise."""
    app = _run()

    app.sidebar.selectbox[0].set_value("pt").run()

    assert app.title[0].value == translate("home.title", "pt")
    assert app.sidebar.selectbox[0].label == translate("sidebar.language", "pt")


@pytest.mark.parametrize("language", available_languages())
def test_no_translated_label_is_stored_in_session_state(language: str):
    """Rótulo traduzido em `session_state` envelhece: ele sobreviveria à troca de língua.

    O estado guarda o que a análise produziu (`archive`, `ignore_folders`, ...), nunca
    o texto da tela.
    """
    app = _run(language)

    stored = {
        value for value in app.session_state.filtered_state.values() if isinstance(value, str)
    }

    assert stored.isdisjoint(load_locale(language).values())
