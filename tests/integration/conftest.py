"""
Ferramentas comuns aos testes que rodam a interface de verdade.

Ler "o que a tela mostra" e "o que pertence a outra língua" é a mesma pergunta na
home e no relatório, então a resposta mora aqui em vez de ser copiada nos dois.

Responsabilidades:
- Colher todo texto que uma execução do `AppTest` põe na tela.
- Nomear os rótulos que pertencem às outras línguas, e só a elas.
"""

from typing import Callable

import pytest
from streamlit.testing.v1 import AppTest

from utils.i18n import available_languages, load_locale, translate

# Elementos que carregam texto lido pelo usuário. `label`, `value` e `options`
# cobrem rótulo de widget, texto escrito na tela e opção de escolha.
TEXT_BEARING_ELEMENTS = (
    "title",
    "header",
    "subheader",
    "markdown",
    "caption",
    "button",
    "radio",
    "selectbox",
    "multiselect",
    "text_input",
    "checkbox",
    "metric",
    "tabs",
    "info",
    "warning",
    "error",
)


@pytest.fixture
def visible_text() -> Callable[[AppTest], set[str]]:
    """Todo texto que a tela mostra, rótulo de widget e opção incluídos."""

    def collect(app: AppTest) -> set[str]:
        found: set[str] = set()

        for kind in TEXT_BEARING_ELEMENTS:
            for element in getattr(app, kind, []):
                for attribute in ("label", "value"):
                    text = getattr(element, attribute, None)
                    if isinstance(text, str):
                        found.add(text)

                found.update(
                    option
                    for option in getattr(element, "options", [])
                    if isinstance(option, str)
                )

        return found | _table_text(app)

    return collect


def _table_text(app: AppTest) -> set[str]:
    """Cabeçalho e células das tabelas da tela.

    A tabela do relatório carrega rótulo em dois lugares — o nome da coluna e o
    valor de Status e Origem —, e nenhum deles é `label` nem `value` de widget.
    Sem varrê-la, uma célula em português passaria pela guarda de língua sem ser
    vista, que foi exatamente o que aconteceu enquanto `normalize` devolvia frase.
    """
    found: set[str] = set()

    for table in getattr(app, "table", []):
        frame = table.value
        if frame is None:
            continue

        found.update(str(column) for column in frame.columns)
        for column in frame.columns:
            found.update(str(cell) for cell in frame[column])

    return found


@pytest.fixture
def foreign_labels() -> Callable[[str], set[str]]:
    """Rótulos que pertencem às outras línguas, e só a elas.

    `language.name` fica de fora de propósito: o seletor mostra cada língua no
    próprio nome, então ver "Português" com a tela em inglês é o comportamento
    pedido (ADR-0009), não vazamento.
    """

    def compute(language: str) -> set[str]:
        own = set(load_locale(language).values())
        endonyms = {translate("language.name", other) for other in available_languages()}

        foreign = {
            value
            for other in available_languages()
            if other != language
            for value in load_locale(other).values()
        }

        return foreign - own - endonyms

    return compute
