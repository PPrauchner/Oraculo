"""
Guarda que nenhum emoji volta ao codigo nem aos textos de tela.

O projeto usava emoji em tres papeis (chave, valor de controle, decoracao); os dois
primeiros ja morreram, e a decoracao migrou para `utils/icons.py` como SVG que herda
`currentColor` (issue #45). Icone e decisao de apresentacao e sai em SVG, nao em
pictograma colado numa string -- um SVG acompanha os temas claro e escuro sem duplicar
texto por variante.

Responsabilidades:
- Varrer o codigo (`.py`) e os textos de tela (`locales/*.json`) atras de emoji.
- Falhar apontando o arquivo, para que a regressao seja localizavel.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Faixas Unicode de emoji e pictogramas, como pares de codepoint. Ficam em inteiros (e
# a classe de regex nasce de `chr()`) para que este proprio arquivo, que proibe emoji,
# nao contenha nenhum. As faixas casam os pictogramas coloridos e deixam de fora as
# setas (U+2190-U+21FF), o reticencias vertical (U+22EE) e as letras acentuadas do
# portugues -- todas abaixo de U+2600 ou fora dos intervalos.
EMOJI_RANGES = [
    (0x2600, 0x26FF),    # simbolos diversos
    (0x2700, 0x27BF),    # dingbats
    (0x2B00, 0x2BFF),    # setas e formas
    (0xFE0F, 0xFE0F),    # seletor de variacao (emoji presentation)
    (0x1F300, 0x1F5FF),  # simbolos e pictogramas
    (0x1F600, 0x1F64F),  # emoticons
    (0x1F680, 0x1F6FF),  # transporte e mapas
    (0x1F900, 0x1F9FF),  # simbolos suplementares
    (0x1FA70, 0x1FAFF),  # pictogramas estendidos
]
EMOJI = re.compile(
    "[" + "".join(f"{chr(lo)}-{chr(hi)}" for lo, hi in EMOJI_RANGES) + "]"
)

# O que o usuario le e o que roda a analise: codigo-fonte e os textos de tela que ele
# renderiza. `docs/` fica de fora de proposito -- e documentacao, e o historico
# (`grills_logs`, ADRs) registra o estado antigo, emoji e tudo (ver CLAUDE.md).
SCANNED_FILES = sorted(
    [ROOT / "main.py"]
    + list((ROOT / "core").rglob("*.py"))
    + list((ROOT / "utils").rglob("*.py"))
    + list((ROOT / "pages").rglob("*.py"))
    + list((ROOT / "tests").rglob("*.py"))
    + list((ROOT / "locales").glob("*.json"))
)


def test_scanned_files_were_found():
    """Se a varredura nao achar nada, a guarda abaixo passa por vacuidade."""
    assert SCANNED_FILES


@pytest.mark.parametrize("path", SCANNED_FILES, ids=lambda path: path.name)
def test_source_has_no_emoji(path: Path):
    """Nenhum emoji no codigo nem nos textos de tela (issue #45)."""
    found = EMOJI.findall(path.read_text(encoding="utf-8"))

    assert found == []
