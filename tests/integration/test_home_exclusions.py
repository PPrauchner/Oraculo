"""
A área de Exclusões exercitada pela tela, nos dois estados que ela tem.

A Exclusão não tem o que oferecer antes de existir um Projeto-Alvo: `folder_list` só
é preenchida quando uma fonte carrega. Enquanto isso, o multiselect ficava na tela
com "No options to select" — um controle que parece defeito, quando o que existe é
uma etapa ainda não cumprida.

Responsabilidades:
- Guardar que a área não mostra controle vazio antes da fonte.
- Guardar que ela explica, em qualquer língua, o que falta para as pastas aparecerem.
- Guardar que, com fonte carregada, escolher Exclusões funciona como antes.
- Guardar que trocar de Projeto-Alvo descarta a Exclusão que a nova fonte não tem.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from utils.i18n import available_languages, translate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_PAGE = str(PROJECT_ROOT / "pages" / "home.py")

# A chave que explica por que ainda não há pasta a oferecer.
NO_SOURCE_HINT = "home.settings.no_source"


def _run(language: str = "en") -> AppTest:
    """Abre a página inicial na língua pedida, como um navegador abriria."""
    app = AppTest.from_file(HOME_PAGE, default_timeout=30)
    app.query_params["lang"] = language

    return app.run()


@pytest.mark.parametrize("language", available_languages())
def test_no_empty_exclusion_control_before_a_target_project(language: str):
    """Sem fonte, nenhum multiselect: dropdown sem opção lê-se como defeito.

    O corpo da tela é o que importa aqui — a barra lateral tem controles próprios,
    que existem desde a primeira renderização e não dependem de Projeto-Alvo.
    """
    app = _run(language)

    assert app.main.multiselect == []


@pytest.mark.parametrize("language", available_languages())
def test_the_exclusion_area_says_what_is_missing(language: str):
    """Esconder o controle sem dizer nada deixaria um card vazio, que também lê mal.

    A frase nomeia a causa — as pastas aparecem depois que a fonte entra —, então o
    estado vazio vira etapa da sequência em vez de defeito.
    """
    app = _run(language)

    captions = [caption.value for caption in app.main.caption]

    assert translate(NO_SOURCE_HINT, language) in captions


def _with_target_project(directory: Path, language: str = "en") -> AppTest:
    """Abre a home, carrega um Projeto-Alvo por diretório e só então troca de língua.

    A ordem não é decorativa. `set_value` num radio reexecuta o `format_func` fora da
    execução do script, onde `?lang=` ainda não vale — o rótulo sai em inglês e não
    casa com as opções já desenhadas na outra língua. Carregar em inglês e trocar
    depois pelo seletor é também o caminho que o usuário percorre.
    """
    app = _run()
    app.radio[0].set_value("directory").run()
    app.text_input[0].set_value(str(directory)).run()

    if language != "en":
        app.sidebar.selectbox[0].set_value(language).run()

    return app


def test_a_loaded_target_project_brings_the_exclusion_control_back():
    """Esconder o controle é sobre não ter o que oferecer, não sobre tirar a função.

    O próprio ORÁCULO é Projeto-Alvo válido, então a fonte é real e as pastas
    oferecidas são as que ele tem de verdade.
    """
    app = _with_target_project(PROJECT_ROOT)

    assert len(app.main.multiselect) == 1
    assert app.main.multiselect[0].options == app.session_state["folder_list"]


def test_choosing_an_exclusion_still_works():
    """A escolha do usuário chega ao estado que a auditoria lê."""
    app = _with_target_project(PROJECT_ROOT)
    excluded = app.session_state["folder_list"][:2]

    app.main.multiselect[0].set_value(excluded).run()

    assert app.session_state["ignore_folders"] == excluded


@pytest.mark.parametrize("language", available_languages())
def test_the_hint_gives_way_to_the_control(language: str):
    """A frase é do estado vazio: com fonte carregada ela sai da tela.

    Dica que sobrevive ao fato que ela explicava vira ruído ao lado do controle real.
    """
    app = _with_target_project(PROJECT_ROOT, language)

    captions = [caption.value for caption in app.main.caption]

    assert translate(NO_SOURCE_HINT, language) not in captions


def _fake_project(root: Path, folder: str) -> Path:
    """Um Projeto-Alvo mínimo válido, com uma única pasta excluível.

    Precisa de um `.py` e de uma Declaração fora das Exclusões — é o que
    `validate_project_structure` exige para a fonte ser aceita.
    """
    root.mkdir(parents=True)
    (root / "main.py").write_text("import os\n", encoding="utf-8")
    (root / "requirements.txt").write_text("requests\n", encoding="utf-8")

    (root / folder).mkdir()
    (root / folder / "mod.py").write_text("import sys\n", encoding="utf-8")

    return root


def test_switching_target_project_drops_an_exclusion_the_new_source_lacks(tmp_path: Path):
    """Exclusão marcada que a nova fonte não tem quebraria o multiselect.

    Trocar de Projeto-Alvo troca o conjunto de pastas oferecidas, e a seleção antiga
    sobrevive em `session_state` — é essa sobra que a reconciliação descarta.
    """
    first = _fake_project(tmp_path / "first", "alpha")
    second = _fake_project(tmp_path / "second", "beta")

    app = _with_target_project(first)
    app.main.multiselect[0].set_value(["alpha"]).run()
    assert app.session_state["ignore_folders"] == ["alpha"]

    app.text_input[0].set_value(str(second)).run()

    assert app.session_state["folder_list"] == ["beta"]
    assert "alpha" not in app.session_state["ignore_folders"]


def test_dropping_the_source_returns_the_area_to_its_empty_state(tmp_path: Path):
    """O estado vazio é reversível: esquecer a fonte traz a frase de volta.

    Sem isto, a área ficaria presa no controle da fonte anterior — um multiselect
    oferecendo pastas de um Projeto-Alvo que a tela já não tem.
    """
    app = _with_target_project(_fake_project(tmp_path / "first", "alpha"))
    assert len(app.main.multiselect) == 1

    app.text_input[0].set_value("").run()

    assert app.main.multiselect == []
    assert translate(NO_SOURCE_HINT, "en") in [
        caption.value for caption in app.main.caption
    ]
