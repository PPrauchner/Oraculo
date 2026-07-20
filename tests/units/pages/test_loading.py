"""
Testes estruturais da página de carregamento.

Garante que a função de renderização do carregamento tenha uma única
definição — a versão duplicada é código morto que o Python descarta e
apenas engana quem lê — e que o carregamento não encene espera nem emita
HTML desbalanceado.
"""

import ast
import re
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


def test_loader_nao_estoura_a_altura_da_viewport():
    """O bloco de carregamento cabe na tela, sem forçar barra de rolagem.

    O `min-height: 150vh` deixava a tela de carregamento 1,5x mais alta que a
    viewport: a auditoria inteira rodava com o usuário olhando para uma barra de
    rolagem que não levava a lugar nenhum (issue #39).
    """
    source = LOADING_MODULE.read_text(encoding="utf-8")

    oversized = re.findall(r"(?:min-)?height:\s*(\d+)vh", source)

    assert [size for size in oversized if int(size) > 100] == []


def test_o_anel_do_loader_e_redondo():
    """O "ring" é um círculo: `border-radius: 50%`, não 70%."""
    source = LOADING_MODULE.read_text(encoding="utf-8")

    assert "border-radius: 70%" not in source
    assert "border-radius: 50%" in source


def test_nenhuma_pagina_injeta_folha_de_estilo_propria():
    """Nenhuma página redefine a aparência por conta própria.

    `visual_css()` pintava dropzone e botão com um azul só dela, brigando com o
    tema. Aparência agora vem de `.streamlit/config.toml`; o único `<style>` que
    sobra é o layout do loader, que não tem equivalente declarativo.
    """
    offenders = [
        module.name
        for module in PAGES_DIR.glob("*.py")
        if _count_function_definitions(module.read_text(encoding="utf-8"), "visual_css")
    ]

    assert offenders == []
