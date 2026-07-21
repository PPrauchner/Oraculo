"""
Guarda a fronteira entre `core/` e a apresentação.

O invariante "`core/` não conhece Streamlit" era respeitado ao pé da letra e violado
na prática: nenhum módulo importava `streamlit`, mas `core/ingestion/` escolhia o
ícone e a língua (português) das mensagens de erro. O acoplamento não estava
no import; estava na string (ADR-0010).

Responsabilidades:
- Guardar que `core/` não importa Streamlit.
- Guardar que `core/` não decide ícone — nenhum emoji nas suas strings.
- Guardar que `core/` não alcança o tradutor — a língua é decisão de tela.
"""

import ast
import re
from pathlib import Path

import pytest

CORE_DIR = Path(__file__).resolve().parents[2] / "core"

# Faixas Unicode de emoji e pictogramas, como pares de codepoint. Ficam em inteiros (e a
# classe de regex nasce de `chr()`) para que este próprio arquivo, que proíbe emoji em
# `core/`, não contenha nenhum. Um deles em `core/` significa que a camada de domínio
# voltou a decidir como o erro aparece na tela.
EMOJI_RANGES = [
    (0x2600, 0x26FF),    # símbolos diversos
    (0x2700, 0x27BF),    # dingbats
    (0x2B00, 0x2BFF),    # setas e formas
    (0xFE0F, 0xFE0F),    # seletor de variação (emoji presentation)
    (0x1F300, 0x1F5FF),  # símbolos e pictogramas
    (0x1F600, 0x1F64F),  # emoticons
    (0x1F680, 0x1F6FF),  # transporte e mapas
    (0x1F900, 0x1F9FF),  # símbolos suplementares
    (0x1FA70, 0x1FAFF),  # pictogramas estendidos
]
EMOJI = re.compile(
    "[" + "".join(f"{chr(lo)}-{chr(hi)}" for lo, hi in EMOJI_RANGES) + "]"
)

CORE_MODULES = sorted(CORE_DIR.rglob("*.py"))

# O tradutor da interface. `core/` importa `utils` o tempo todo — constantes e
# `TypedDict` moram lá —, e é este módulo, e só ele, que a fronteira proíbe.
TRANSLATOR = "utils.i18n"


def _imported_paths(source: str) -> set[str]:
    """Caminhos completos de módulo importados por um arquivo.

    O de topo não serve aqui: `utils` é importado por `core/` o tempo todo (as
    constantes e os `TypedDict` moram lá), e é só `utils.i18n` que a fronteira
    proíbe.
    """
    paths = set()

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            paths.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            paths.add(node.module)

    return paths


def _imported_modules(source: str) -> set[str]:
    """Nomes de módulo de topo importados por um arquivo."""
    names = set()

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])

    return names


def test_core_modules_were_found():
    """Se a varredura não achar nada, as guardas abaixo passam por vacuidade."""
    assert CORE_MODULES


@pytest.mark.parametrize("module", CORE_MODULES, ids=lambda path: path.name)
def test_core_does_not_import_streamlit(module: Path):
    """Erro em `core/` é retorno ou exceção; quem chama `st.error()` é `pages/`."""
    assert "streamlit" not in _imported_modules(module.read_text(encoding="utf-8"))


@pytest.mark.parametrize("module", CORE_MODULES, ids=lambda path: path.name)
def test_core_does_not_choose_an_icon(module: Path):
    """Ícone é decisão de apresentação: `core/` devolve código, não ícone (ADR-0010)."""
    found = EMOJI.findall(module.read_text(encoding="utf-8"))

    assert found == []


@pytest.mark.parametrize("module", CORE_MODULES, ids=lambda path: path.name)
def test_core_cannot_reach_the_translator(module: Path):
    """`core/` não importa `utils.i18n` — nem para traduzir, nem por engano.

    É a guarda estrutural do CSV como contrato (ADR-0008). Comparar dois exports
    byte a byte não basta: `CSV_HEADER` é montado uma vez na importação, então um
    `t()` ali dentro congelaria a primeira língua e os dois exports sairiam iguais
    — idênticos entre si e errados para todo mundo que não abrisse o app em inglês.
    Verificado: a comparação byte a byte deixa essa sabotagem passar, esta não.

    A regra é mais larga que o CSV de propósito. Nada em `core/` decide língua: o
    que ele devolve é código estável e dado, e quem traduz é `utils/display.py` ou
    `utils/messages.py` (ADR-0010).
    """
    assert TRANSLATOR not in _imported_paths(module.read_text(encoding="utf-8"))
