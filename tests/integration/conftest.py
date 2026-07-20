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

        return found

    return collect


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
