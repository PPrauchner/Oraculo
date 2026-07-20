"""
O relatório exercitado nas duas línguas, com a análise já feita.

É a tela com mais rótulo por metro quadrado — abas, métricas, gráfico e diálogo de
exportação — e a única em que o rótulo também era chave: de dicionário, de
`session_state` e do mapa de cores do donut. Traduzir a chave junto com o texto
desmontaria tudo isso em silêncio, então aqui se guarda a separação entre a
identidade estável da categoria e o rótulo que ela mostra (ADR-0009).

Responsabilidades:
- Guardar que o relatório inteiro fala a língua de `?lang=`.
- Guardar que a identidade da categoria não acompanha a língua.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from utils.i18n import available_languages, translate

REPORT_PAGE = str(Path(__file__).resolve().parents[2] / "pages" / "report.py")

# Uma auditoria pronta, no formato que `pages/loading.py` deixa em `session_state`.
# As chaves de dado seguem em português porque o esquema é contrato e não acompanha
# o seletor (ADR-0008) — é justamente o que separa dado de rótulo.
OUTDATED_DEPENDENCY = {
    "package": "requests",
    "used_version": "2.31.0",
    "pypi_version": "2.32.0",
    "status": "Desatualizado",
    "Tamanho": 100_000,
    "Idade": 400,
    "Origem": "Production",
}

ZOMBIE_DEPENDENCY = {
    "package": "rich",
    "used_version": "13.0.0",
    "pypi_version": "13.0.0",
    "status": "Atualizado",
    "Tamanho": 50_000,
    "Idade": 100,
    "Origem": "Production",
}

CATEGORY_KEYS = (
    "report.category.all_dependencies",
    "report.category.zombies",
    "report.category.ghosts",
    "report.category.outdated",
)


def _run(language: str) -> AppTest:
    """Abre o relatório com uma análise já concluída, na língua pedida."""
    app = AppTest.from_file(REPORT_PAGE, default_timeout=60)
    app.query_params["lang"] = language

    app.session_state["analysis_complete"] = True
    app.session_state["all_dependencies"] = [OUTDATED_DEPENDENCY, ZOMBIE_DEPENDENCY]
    app.session_state["zombies"] = [ZOMBIE_DEPENDENCY]
    app.session_state["ghosts"] = []

    return app.run()


@pytest.mark.parametrize("language", available_languages())
def test_the_report_titles_every_category_in_the_language_of_the_url(language: str):
    """Aba e métrica saem do locale, na ordem em que o relatório as apresenta."""
    app = _run(language)
    expected = [translate(key, language) for key in CATEGORY_KEYS]

    assert app.title[0].value == translate("report.title", language)
    assert [tab.label for tab in app.tabs] == expected
    assert [metric.label for metric in app.metric] == expected


@pytest.mark.parametrize("language", available_languages())
def test_the_report_shows_no_label_from_another_language(
    language: str, visible_text, foreign_labels
):
    """O relatório também fala uma língua só, do título ao botão de exportar."""
    assert visible_text(_run(language)).isdisjoint(foreign_labels(language))


@pytest.mark.parametrize("language", available_languages())
def test_the_export_dialog_is_keyed_by_category_not_by_label(language: str):
    """A caixa marcada é lembrada pela categoria, não pelo texto que ela exibe.

    Com o rótulo na chave, trocar de língua criaria um `cb_*` novo em
    `session_state` e a seleção do usuário voltaria ao padrão sozinha — sem erro,
    sem aviso e sem ninguém ter desmarcado nada.
    """
    app = _run(language)
    app.button[0].click().run()

    checked = {key for key in app.session_state.filtered_state if key.startswith("cb_")}

    assert app.exception == []
    assert checked == {
        "cb_all_dependencies",
        "cb_zombies",
        "cb_ghosts",
        "cb_outdated",
    }


@pytest.mark.parametrize("language", available_languages())
def test_the_download_label_counts_the_rows_it_will_export(language: str):
    """O rótulo do download interpola contagem e extensão a partir do locale.

    O texto muda de língua; o número de linhas, não — ele descreve o arquivo, que é
    idêntico nas duas (ADR-0008).
    """
    app = _run(language)
    app.button[0].click().run()

    label = app.get("download_button")[0].label

    assert label == translate("report.export.download", language).format(
        count=2, extension="csv"
    )
