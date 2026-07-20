"""
Guarda a fronteira entre `core/` e a apresentação.

O invariante "`core/` não conhece Streamlit" era respeitado ao pé da letra e violado
na prática: nenhum módulo importava `streamlit`, mas `core/ingestion/` escolhia o
ícone (`❌`) e a língua (português) das mensagens de erro. O acoplamento não estava
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

# Blocos Unicode de emoji e pictogramas. Um deles em `core/` significa que a camada
# de domínio voltou a decidir como o erro aparece na tela.
EMOJI = re.compile(
    "["
    "☀-⛿"  # símbolos diversos (⚠, ⛔)
    "✀-➿"  # dingbats (❌, ✅)
    "⬀-⯿"  # setas e formas
    "️"  # seletor de variação (emoji presentation)
    "\U0001f300-\U0001f5ff"  # símbolos e pictogramas
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f680-\U0001f6ff"  # transporte e mapas
    "\U0001f900-\U0001f9ff"  # símbolos suplementares
    "\U0001fa70-\U0001faff"  # pictogramas estendidos
    "]"
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
    """Ícone é decisão de apresentação: `core/` devolve código, não `❌` (ADR-0010)."""
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
