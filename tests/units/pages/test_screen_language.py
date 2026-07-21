"""
Guarda de que a tela inteira fala pelo locale, e não por literal cravado no módulo.

O seletor de língua só é honesto se **toda** frase que o usuário lê passar por `t()`
(ADR-0009). Enquanto sobrar uma frase literal em `pages/`, a interface fica bilíngue:
o seletor diz "English" e a tela responde em português. Este teste é o que transforma
"esqueci de traduzir uma tela" em falha de build.

Responsabilidades:
- Varrer os módulos de tela atrás de literal que pareça frase dita ao usuário.
- Deixar passar marcação e estilo, que são layout e não se traduzem.
"""

import ast
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Os módulos que desenham tela: as páginas, a barra lateral e o ponto de entrada
# (onde vivem os títulos de `st.navigation`).
SCREEN_MODULES = sorted(
    [PROJECT_ROOT / "main.py", PROJECT_ROOT / "utils" / "sidebar.py"]
    + list((PROJECT_ROOT / "pages").glob("*.py"))
)

# Uma tag HTML completa. Some antes da conferência para que a prosa *dentro* da
# marcação continue visível ao teste — era ali que "Analysis in Progress..." se
# escondia, dentro do mesmo literal que abre a `<div>` do carregamento.
HTML_TAG = re.compile(r"<[^>]*>")

# Restos de marcação ou estilo. Um literal que ainda os contém depois da limpeza é
# HTML partido por interpolação ou bloco CSS — layout, não frase.
MARKUP_MARKERS = ("<", "{", "}", ";")


def _docstring_ids(tree: ast.AST) -> set[int]:
    """Identidade dos literais que são docstring.

    Docstring fala com quem lê o código, não com quem usa a tela — e é escrita em
    português por convenção do projeto.
    """
    holders = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    found = set()

    for node in ast.walk(tree):
        if not isinstance(node, holders) or not node.body:
            continue

        first = node.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            found.add(id(first.value))

    return found


def _is_prose(value: str) -> bool:
    """Decide se um literal parece uma frase dita ao usuário.

    Frase é: sobra marcação nenhuma, sobram pelo menos duas palavras e há letra no
    meio. Duas palavras — e não uma — porque nome próprio (`ORÁCULO`), caminho de
    módulo (`pages/home.py`) e chave de dado (`Pacote`) são identificadores, não
    texto a traduzir.
    """
    stripped = HTML_TAG.sub(" ", value)

    if any(marker in stripped for marker in MARKUP_MARKERS):
        return False

    return len(stripped.split()) >= 2 and any(char.isalpha() for char in stripped)


def _prose_literals(source: str) -> list[str]:
    """Literais de um módulo que parecem frase dita ao usuário."""
    tree = ast.parse(source)
    docstrings = _docstring_ids(tree)

    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
        and _is_prose(node.value)
    ]


def test_screen_modules_were_found():
    """Se a varredura não achar nada, a guarda abaixo passa por vacuidade."""
    assert SCREEN_MODULES


@pytest.mark.parametrize("module", SCREEN_MODULES, ids=lambda path: path.name)
def test_no_user_prose_is_written_straight_into_a_screen_module(module: Path):
    """Toda frase que o usuário lê vem do locale, nenhuma vem cravada no módulo.

    O rótulo resolve na renderização (`t()`), então trocar de língua retraduz a tela
    inteira de uma vez — e acrescentar um idioma continua sendo acrescentar um
    arquivo, sem tocar em código (ADR-0009).
    """
    found = _prose_literals(module.read_text(encoding="utf-8"))

    assert found == []
