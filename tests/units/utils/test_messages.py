"""
Testes da tradução de código de erro para a frase que o usuário lê.

`core/` devolve `(código, parâmetros)` e não sabe em que língua o erro fala
(ADR-0010); é aqui que o código vira texto — pelo mesmo `locales/*.json` que traduz
o resto da tela (ADR-0009), e não por um dicionário paralelo.
"""

import ast
from pathlib import Path

import pytest

import utils.i18n
from utils.i18n import DEFAULT_LANGUAGE, available_languages, load_locale, translate
from utils.messages import ERROR_KEY_PREFIX, error_key, format_error

INGESTION_DIR = Path(__file__).resolve().parents[3] / "core" / "ingestion"


def _screen_language(monkeypatch: pytest.MonkeyPatch, language: str) -> None:
    """Finge a língua da requisição atual, que é o que `?lang=` decide."""
    monkeypatch.setattr(utils.i18n.st, "query_params", {"lang": language})


@pytest.mark.parametrize("language", available_languages())
def test_format_error_speaks_the_language_of_the_screen(
    monkeypatch: pytest.MonkeyPatch, language: str
):
    """Um caminho de tradução, não dois: o erro sai na língua do resto da tela.

    Antes o texto de erro vinha de um `dict` monolíngue em módulo Python, alheio ao
    seletor — a tela trocava de língua e o erro continuava em português.
    """
    _screen_language(monkeypatch, language)

    assert format_error(("source_missing", {})) == translate(
        error_key("source_missing"), language
    )


def test_format_error_interpolates_the_parameters_of_the_code():
    """O parâmetro entra na frase: o dado vem de `core/`, a redação daqui."""
    rendered = format_error(("directory_not_found", {"path": "C:/alvo"}))

    assert "C:/alvo" in rendered


@pytest.mark.parametrize(
    "language, expected",
    [
        ("en", "Path not found: C:/alvo"),
        ("pt", "Caminho não encontrado: C:/alvo"),
    ],
)
def test_format_error_interpolates_in_the_language_of_the_screen(
    monkeypatch: pytest.MonkeyPatch, language: str, expected: str
):
    """O erro interpolado sai na língua da tela: inglês em `en`, português em `pt`.

    Junta num caso só as duas garantias que a mensagem de erro no locale fecha —
    resolver pelo código na língua da requisição e interpolar o parâmetro de
    `core/`. Se `format_error` ignorasse a língua da tela, `pt` renderizaria o texto
    inglês com o caminho e este teste falharia.
    """
    _screen_language(monkeypatch, language)

    assert format_error(("directory_not_found", {"path": "C:/alvo"})) == expected


def test_format_error_renders_a_code_without_parameters():
    assert format_error(("source_missing", {})) == translate(
        error_key("source_missing"), DEFAULT_LANGUAGE
    )


def test_format_error_falls_back_to_the_code_when_it_has_no_message():
    """Código sem texto aparece cru — sem o prefixo de chave, que não diz nada a ninguém.

    Um erro de tradução não pode esconder o erro que o usuário precisa ver, nem
    trocá-lo por um identificador de locale.
    """
    assert format_error(("codigo_inexistente", {})) == "codigo_inexistente"


def test_format_error_survives_a_missing_parameter():
    """Parâmetro faltando não pode derrubar a tela: a frase sai como está."""
    assert format_error(("directory_not_found", {})) == translate(
        error_key("directory_not_found"), DEFAULT_LANGUAGE
    )


def test_error_key_is_namespaced_inside_the_locale():
    """O código de erro entra no locale sob um prefixo próprio.

    Sem ele, um código de `core/` poderia colidir com uma chave de rótulo de tela.
    """
    assert error_key("empty_path") == f"{ERROR_KEY_PREFIX}empty_path"


def _codes_returned_by(module: Path) -> set[str]:
    """Códigos de erro que um módulo devolve como `("codigo", {...})`.

    Casa a forma exata do `IngestionError`: tupla de dois elementos cujo primeiro
    é uma string literal e o segundo, um dicionário.
    """
    tree = ast.parse(module.read_text(encoding="utf-8"))

    return {
        node.elts[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Tuple)
        and len(node.elts) == 2
        and isinstance(node.elts[0], ast.Constant)
        and isinstance(node.elts[0].value, str)
        and isinstance(node.elts[1], ast.Dict)
    }


@pytest.mark.parametrize("language", available_languages())
def test_every_code_that_ingestion_can_return_has_a_message(language: str):
    """Código sem tradução chegaria ao usuário como identificador cru.

    É a mesma garantia que ADR-0009 pede entre `locales/`: falha de build em vez de
    descoberta na tela. Vale para toda língua — um código traduzido só no inglês
    deixaria o usuário em português lendo inglês no pior momento possível.
    """
    emitted = set()
    for module in INGESTION_DIR.glob("*.py"):
        emitted |= _codes_returned_by(module)

    assert emitted, "nenhum código encontrado — o extrator do teste parou de casar"
    assert {error_key(code) for code in emitted} <= set(load_locale(language))
