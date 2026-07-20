"""
Testes estruturais da página de carregamento.

Garante que a função de renderização do carregamento tenha uma única
definição — a versão duplicada é código morto que o Python descarta e
apenas engana quem lê — e que o carregamento não encene espera nem emita
HTML desbalanceado.
"""

import ast
from pathlib import Path

PAGES_DIR = Path(__file__).resolve().parents[3] / "pages"
LOADING_MODULE = PAGES_DIR / "loading.py"


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


def _sleep_calls(source: str) -> list[str]:
    """Nomes das chamadas a `sleep` (qualificadas ou não) no módulo."""
    tree = ast.parse(source)
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr == "sleep":
            calls.append(f"{ast.unparse(node.func)}()")
        elif isinstance(node.func, ast.Name) and node.func.id == "sleep":
            calls.append("sleep()")
    return calls


def test_nenhuma_pagina_encena_espera():
    """O progresso é dirigido pelo trabalho real, sem atraso artificial.

    O tempo percebido da auditoria era ~90% `time.sleep()`. Cada etapa avança
    quando a etapa correspondente termina de fato; projeto pequeno piscar é a
    ferramenta sendo rápida, não um defeito a "consertar" com atraso.
    """
    offenders = {
        module.name: found
        for module in PAGES_DIR.glob("*.py")
        if (found := _sleep_calls(module.read_text(encoding="utf-8")))
    }

    assert offenders == {}


def test_html_do_loader_fecha_as_divs_que_abre():
    """O loader fecha exatamente as `<div>` que abre, sem fechamento órfão."""
    source = LOADING_MODULE.read_text(encoding="utf-8")

    assert source.count("<div") == source.count("</div>")
