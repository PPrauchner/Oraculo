"""
O Projeto de Exemplo exercitado pela tela: da home ao relatório, num clique.

Hospedado, o ORÁCULO só audita o que o visitante enviar, e quem chega para
conhecê-lo raramente tem um projeto Python à mão (issue #58). O exemplo segue o
mesmo pipeline de qualquer Projeto-Alvo, sem upload, sem caminho digitado e sem
clicar em "Executar".

Responsabilidades:
- Guardar que um clique leva ao relatório do exemplo, com e sem o modo hospedado.
- Guardar que o exemplo substitui o Projeto-Alvo anterior e roda sem Exclusões.
- Guardar que a identidade do exemplo na exportação não muda com a língua.

O PyPI é substituído por um dublê determinístico: a suíte não usa a rede.

Com o rádio de modo na tela, um clique do `AppTest` reavalia o `format_func` fora da
execução do script, onde `?lang=` não vale (ver `test_home_exclusions`): por isso o
clique em outra língua acontece no modo hospedado, que não tem o rádio.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.ingestion.sample_project import SAMPLE_PROJECT_NAME
from core.report.normalization import build_export_rows
from utils.hosting import HOSTED_VARIABLE
from utils.i18n import available_languages, translate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# A entrada de verdade: `st.switch_page` só acha a página com `st.navigation` rodando.
ENTRY_POINT = str(PROJECT_ROOT / "main.py")
SAMPLE_ACTION = "home.sample"


@pytest.fixture(autouse=True)
def fake_pypi(monkeypatch):
    """Toda versão do PyPI é a mais recente possível: sem rede, e o exemplo envelhece."""
    monkeypatch.setattr(
        "core.analysis.outdated_analizer.fetch_package_data",
        lambda package_name: {"info": {"version": "99.0.0"}, "releases": {}},
    )


@pytest.fixture
def hosted(monkeypatch):
    """Liga o modo hospedado como o Streamlit Cloud ligaria: pelo ambiente."""
    monkeypatch.setenv(HOSTED_VARIABLE, "true")


def _home(language: str = "en") -> AppTest:
    """A aplicação aberta na home, na língua pedida."""
    app = AppTest.from_file(ENTRY_POINT, default_timeout=60)
    app.query_params["lang"] = language

    return app.run()


def _click_sample(app: AppTest, language: str = "en") -> AppTest:
    """Um clique no exemplo — e nada mais. O botão é achado pelo rótulo da tela."""
    label = translate(SAMPLE_ACTION, language)
    button = next(button for button in app.main.button if button.label == label)

    return button.click().run()


def _assert_sample_report(app: AppTest) -> None:
    """A tela é o relatório, e o relatório é o do exemplo.

    O título é aceito em qualquer língua: o `st.switch_page` não leva `?lang=`
    adiante, e o que se guarda aqui é a chegada, não a língua.
    """
    report_titles = {translate("report.title", lang) for lang in available_languages()}

    assert not app.exception
    assert app.title[0].value in report_titles
    assert app.session_state["analysis_complete"] is True
    assert app.session_state["project_name"] == SAMPLE_PROJECT_NAME
    assert {dep["package"] for dep in app.session_state["zombies"]} == {"flask"}
    assert {dep["package"] for dep in app.session_state["ghosts"]} == {"numpy"}


def test_one_click_reaches_the_sample_report():
    """Sem upload, sem caminho e sem "Executar": o clique leva ao relatório pronto."""
    _assert_sample_report(_click_sample(_home()))


@pytest.mark.parametrize("language", available_languages())
def test_the_sample_works_in_the_hosted_mode(hosted, language: str):
    """Hospedada, a home esconde o seletor de modo; o exemplo não depende dele."""
    _assert_sample_report(_click_sample(_home(language), language))


def test_the_sample_replaces_the_previous_target_project_and_its_exclusions(
    tmp_path: Path,
):
    """As Exclusões marcadas eram do projeto anterior: o exemplo roda sem nenhuma.

    O projeto anterior tem uma pasta `app`, como o exemplo. Se a Exclusão vazasse,
    o Fantasma do exemplo — importado em `app/` — sumiria do relatório.
    """
    (tmp_path / "main.py").write_text("import requests\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("requests\n", encoding="utf-8")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "util.py").write_text("import os\n", encoding="utf-8")

    app = _home()
    app.radio[0].set_value("directory").run()
    app.text_input[0].set_value(str(tmp_path)).run()
    app.main.multiselect[0].set_value(["app"]).run()

    _assert_sample_report(_click_sample(app))


@pytest.mark.parametrize("language", available_languages())
def test_the_sample_export_carries_a_fixed_project_name(hosted, language: str):
    """A identidade na exportação é contrato (ADR-0008): não acompanha a língua."""
    app = _click_sample(_home(language), language)

    rows = build_export_rows(
        app.session_state["all_dependencies"],
        app.session_state["zombies"],
        app.session_state["ghosts"],
        app.session_state["project_name"],
        app.session_state["analysis_date"],
    )

    assert rows
    assert {row["project"] for row in rows} == {SAMPLE_PROJECT_NAME}
