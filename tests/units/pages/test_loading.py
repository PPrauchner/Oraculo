"""
Testes estruturais da página de carregamento.

Garante que a função de renderização do carregamento tenha uma única
definição — a versão duplicada é código morto que o Python descarta e
apenas engana quem lê.
"""

import ast
from pathlib import Path

LOADING_MODULE = Path(__file__).resolve().parents[3] / "pages" / "loading.py"


def _count_function_definitions(source: str, name: str) -> int:
    tree = ast.parse(source)
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_render_loading_ui_defined_once():
    """Existe uma única definição de _render_loading_ui no módulo."""
    source = LOADING_MODULE.read_text(encoding="utf-8")
    assert _count_function_definitions(source, "_render_loading_ui") == 1
