"""
A home no modo hospedado, exercitada pela tela.

Publicado, o campo de caminho resolveria no servidor, não na máquina de quem usa:
qualquer visitante poderia apontar para uma pasta do container e auditá-la. No modo
hospedado a ingestão por diretório nem aparece nem acontece (ADR-0014); fora dele,
a home segue igual.

Responsabilidades:
- Guardar que, hospedada, a home mostra só o upload, sem rádio nem campo de caminho.
- Guardar que, hospedada, nenhum caminho do disco vira Projeto-Alvo, nem com o
  estado de sessão pedindo o modo diretório.
- Guardar que a guarda mira o caminho digitado, não o tipo da fonte: uma fonte em
  memória e um upload seguem o fluxo normal.
- Guardar que, sem a configuração, os dois modos continuam oferecidos.

Cada teste fixa ou apaga `ORACULO_HOSTED`: o ambiente de quem roda a suíte não muda
o resultado.
"""

import io
import zipfile
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from utils.hosting import HOSTED_VARIABLE
from utils.i18n import available_languages, translate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_PAGE = str(PROJECT_ROOT / "pages" / "home.py")


@pytest.fixture
def hosted(monkeypatch):
    """Liga o modo hospedado como o Streamlit Cloud ligaria: pelo ambiente."""
    monkeypatch.setenv(HOSTED_VARIABLE, "true")


def _app(language: str = "en") -> AppTest:
    """A home na língua pedida, ainda sem rodar."""
    app = AppTest.from_file(HOME_PAGE, default_timeout=30)
    app.query_params["lang"] = language

    return app


def _uploaders(app: AppTest) -> list:
    """Os seletores de arquivo do corpo da tela."""
    return app.main.get("file_uploader")


@pytest.mark.parametrize("language", available_languages())
def test_hosted_home_offers_only_the_upload(hosted, language: str):
    """Com um modo só, o rádio perde o sentido: a home mostra direto o upload."""
    app = _app(language).run()

    assert app.main.radio == []
    assert app.main.text_input == []
    assert len(_uploaders(app)) == 1
    assert not app.exception


def test_hosted_home_reads_no_path_even_when_the_state_asks_for_it(
    hosted, monkeypatch
):
    """Esconder o rádio não basta: o estado de sessão não pode reabrir a porta.

    Estado antigo, teste ou manipulação podem deixar `ingestion_mode == "directory"`
    e um caminho já digitado. O próprio ORÁCULO é Projeto-Alvo válido, então, se a
    guarda falhasse, a fonte carregaria de verdade e as pastas do servidor
    apareceriam nas Exclusões.
    """
    opened: list[str] = []

    def spy(path: str):
        opened.append(path)
        return None, ("directory_not_found", {"path": path})

    monkeypatch.setattr("core.ingestion.source.open_directory", spy)

    app = _app()
    app.session_state["ingestion_mode"] = "directory"
    app.session_state["project_directory"] = str(PROJECT_ROOT)
    app.run()

    assert opened == []
    assert not isinstance(app.session_state["archive"], Path)
    assert app.session_state["folder_list"] == []
    assert app.main.multiselect == []


def _zipped_target_project() -> bytes:
    """Um Projeto-Alvo mínimo válido, compactado como um visitante enviaria."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("alvo-main/main.py", "import requests\n")
        zf.writestr("alvo-main/requirements.txt", "requests\n")
        zf.writestr("alvo-main/tests/test_main.py", "import pytest\n")

    return buffer.getvalue()


def test_hosted_upload_reaches_the_exclusions_and_the_run_button(hosted):
    """O modo hospedado tira um caminho de entrada, não o resto do fluxo."""
    app = _app().run()

    app.main.file_uploader[0].set_value(
        ("alvo.zip", _zipped_target_project(), "application/zip")
    ).run()

    assert app.session_state["archive_is_valid"] is True
    assert app.session_state["project_name"] == "alvo"
    assert len(app.main.multiselect) == 1
    assert "tests" in app.main.multiselect[0].options
    assert translate("home.run", "en") in [button.label for button in app.main.button]


def test_hosted_mode_does_not_refuse_an_in_memory_target_project(hosted, monkeypatch):
    """A guarda mira o caminho digitado, não o tipo da fonte.

    Um Projeto-Alvo em memória (`dict[str, str]`, ADR-0006) não lê o disco de
    ninguém: hospedado, ele precisa seguir até a auditoria como qualquer upload. O
    PyPI fica de fora — o que se guarda aqui é que nada recusa a fonte.
    """
    monkeypatch.setattr(
        "core.analysis.outdated_analizer.analyze_dependency_status",
        lambda dependencies: dependencies,
    )

    app = AppTest.from_file(str(PROJECT_ROOT / "pages" / "loading.py"), default_timeout=30)
    app.session_state["archive"] = {
        "main.py": "import requests\nimport yaml\n",
        "requirements.txt": "requests\nflask\n",
    }
    app.session_state["ignore_folders"] = []
    app.run()

    assert app.main.error == []
    assert app.session_state["analysis_complete"] is True
    assert {dep["package"] for dep in app.session_state["zombies"]} == {"flask"}
    assert {dep["package"] for dep in app.session_state["ghosts"]} == {"yaml"}


@pytest.mark.parametrize("value", [None, "false", "0", ""])
def test_without_the_hosted_mode_both_ways_in_are_offered(monkeypatch, value):
    """Local, nada muda: rádio com os dois modos, nos mesmos textos de sempre."""
    if value is None:
        monkeypatch.delenv(HOSTED_VARIABLE, raising=False)
    else:
        monkeypatch.setenv(HOSTED_VARIABLE, value)

    app = _app().run()

    assert len(app.main.radio) == 1
    assert app.main.radio[0].options == [
        translate("home.mode.upload", "en"),
        translate("home.mode.directory", "en"),
    ]


@pytest.mark.parametrize("language", available_languages())
def test_hosted_intro_does_not_promise_the_directory(hosted, language: str):
    """A linha de apoio não pode oferecer um modo que a tela não tem."""
    app = _app(language).run()

    captions = [caption.value for caption in app.main.caption]

    assert translate("home.intro", language) not in captions
    assert translate("home.intro.hosted", language) in captions


def test_hosted_home_needs_no_secrets_file(hosted):
    """O modo vem do ambiente: sem `secrets.toml`, nem erro nem aviso na home."""
    if (PROJECT_ROOT / ".streamlit" / "secrets.toml").exists():
        pytest.skip("há um secrets.toml local; o cenário é a ausência dele")

    app = _app().run()

    assert not app.exception
    assert app.error == []
    assert app.warning == []
