"""
Guarda que as seções da tela inicial são delimitadas pela API, não por folha de estilo.

Duas colunas anunciadas só por um subcabeçalho sobre o fundo não se leem como seções —
leem-se como texto empilhado. A moldura resolve isso, mas *como* ela chega importa: com
`st.container(border=True)` a borda sai do `borderColor` do tema e acompanha os modos
claro e escuro sozinha, enquanto um `<style>` injetado cravaria uma cor só dela — que foi
exatamente o defeito que a #39 removeu.

Responsabilidades:
- Guardar que as duas seções estão em containers com borda.
- Guardar que a home não desenha aparência por HTML cru.
"""

import ast
from pathlib import Path

HOME_MODULE = Path(__file__).resolve().parents[3] / "pages" / "home.py"


def _bordered_container_calls(source: str) -> list[ast.Call]:
    """Chamadas a `st.container(border=True)` no módulo."""
    tree = ast.parse(source)

    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "container"
        and any(
            keyword.arg == "border" and keyword.value.value is True
            for keyword in node.keywords
            if isinstance(keyword.value, ast.Constant)
        )
    ]


def test_both_home_sections_sit_in_a_bordered_container():
    """Informe o Projeto-Alvo e Configurações são duas seções, e a tela precisa dizer isso."""
    source = HOME_MODULE.read_text(encoding="utf-8")

    assert len(_bordered_container_calls(source)) == 2


def test_the_home_draws_no_appearance_by_raw_html():
    """A moldura veio da API, e não de um `<div>` com estilo embutido.

    A tela inicial não tem nada que só HTML cru resolva — diferente do loader, cujo
    layout não tem equivalente declarativo. Aqui, `unsafe_allow_html` significaria
    aparência cravada à mão, fora do alcance do tema.
    """
    source = HOME_MODULE.read_text(encoding="utf-8")

    assert "unsafe_allow_html" not in source
    assert "<style" not in source
