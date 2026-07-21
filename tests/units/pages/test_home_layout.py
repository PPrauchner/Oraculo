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


def _renderer_of(source: str, key: str) -> str | None:
    """Método do Streamlit que desenha o rótulo de uma chave do locale.

    Args:
        source: Código do módulo de tela.
        key: Chave do locale, como está em `locales/*.json`.

    Returns:
        O nome do método (`title`, `header`, `caption`, …), ou `None` se a chave não
        é desenhada no módulo.
    """
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.args
        ):
            continue

        first = node.args[0]
        if (
            isinstance(first, ast.Call)
            and isinstance(first.func, ast.Name)
            and first.func.id == "t"
            and first.args
            and isinstance(first.args[0], ast.Constant)
            and first.args[0].value == key
        ):
            return node.func.attr

    return None


def test_the_home_title_steps_down_from_the_largest_heading():
    """O título é médio, e não o maior nível disponível.

    Em tela larga o `st.title` domina tudo e achata o resto da hierarquia. Um nível
    abaixo, ele ainda abre a tela mas deixa espaço para as seções existirem —
    `st.header` acima, `st.subheader` das seções logo abaixo (issue #50).
    """
    source = HOME_MODULE.read_text(encoding="utf-8")

    assert _renderer_of(source, "home.title") == "header"
    assert _renderer_of(source, "home.source.header") == "subheader"
    assert _renderer_of(source, "home.settings.header") == "subheader"


def test_the_home_subtitle_reads_as_a_subtitle():
    """A linha sob o título tem peso e cor secundários, e vem da API.

    Como `st.write` ela pesava o mesmo que qualquer texto corrido, e a hierarquia
    título → subtítulo sumia. `st.caption` resolve sem uma linha de CSS: o cinza
    secundário sai do tema e acompanha os modos claro e escuro sozinho.
    """
    source = HOME_MODULE.read_text(encoding="utf-8")

    assert _renderer_of(source, "home.intro") == "caption"


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
