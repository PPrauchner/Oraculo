"""
Testes da tradução de código de erro para a frase que o usuário lê.

`core/` devolve `(código, parâmetros)` e não sabe em que língua o erro fala
(ADR-0010); é aqui que o código vira texto.
"""

import ast
from pathlib import Path

from utils.messages import ERROR_MESSAGES, format_error

INGESTION_DIR = Path(__file__).resolve().parents[3] / "core" / "ingestion"


def test_format_error_interpolates_the_parameters_of_the_code():
    """O parâmetro entra na frase: o dado vem de `core/`, a redação daqui."""
    rendered = format_error(("directory_not_found", {"path": "C:/alvo"}))

    assert "C:/alvo" in rendered


def test_format_error_renders_a_code_without_parameters():
    assert format_error(("source_missing", {})) == ERROR_MESSAGES["source_missing"]


def test_format_error_falls_back_to_the_code_when_it_has_no_message():
    """Código sem texto aparece cru, e não como frase vazia ou KeyError."""
    assert format_error(("codigo_inexistente", {})) == "codigo_inexistente"


def test_format_error_survives_a_missing_parameter():
    """Parâmetro faltando não pode derrubar a tela: a frase sai como está."""
    assert format_error(("directory_not_found", {})) == ERROR_MESSAGES[
        "directory_not_found"
    ]


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


def test_every_code_that_ingestion_can_return_has_a_message():
    """Código sem tradução chegaria ao usuário como identificador cru.

    É o mesmo tipo de garantia que ADR-0009 pede entre `locales/`: falha de build
    em vez de descoberta na tela.
    """
    emitted = set()
    for module in INGESTION_DIR.glob("*.py"):
        emitted |= _codes_returned_by(module)

    assert emitted, "nenhum código encontrado — o extrator do teste parou de casar"
    assert emitted <= set(ERROR_MESSAGES)
