"""
O ORÁCULO auditado por ele mesmo: ele é um Projeto-Alvo válido.

Aqui — e só aqui — ler o `pyproject.toml` vivo do repositório é o ponto, não um
descuido. Um teste de unidade de reader não pode depender do que o repositório
declara hoje (issue #21); um teste de auto-auditoria só existe porque depende.

Responsabilidades:
- Guardar as decisões que a própria Declaração do repositório precisa respeitar.
"""

from pathlib import Path

import pytest

from core.analysis.ghost_analizer import analyze_ghost_dependencies
from core.analysis.zombie_analizer import analyze_zombie_dependencies
from core.parsin.declaration_collector import collect_declarations
from core.parsin.import_parser import parse_imports_with_filter
from core.parsin.readers import parse_pyproject

REPO_ROOT = Path(__file__).resolve().parents[2]

# `tests` é Exclusão: é onde vivem as Dependências de Desenvolvimento (ADR-0003).
IGNORED_FOLDERS = ["tests"]


@pytest.fixture(scope="module")
def auditoria() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Varre o repositório uma vez e devolve o par (declaradas, importadas).

    As duas guardas abaixo consomem o mesmo par, o que preserva a proteção mútua
    entre elas: um `declared` vazio faz todo import virar Fantasma e reprova a
    guarda de Fantasma; um `imports` vazio faz toda Dependência de Produção virar
    Zumbi e reprova a guarda de Zumbi. Por isso a fixture não filtra nem substitui
    resultado vazio — mascarar isso desarmaria as duas.

    Returns:
        Tupla (Dependências Declaradas, Imports Raiz) do próprio repositório.
    """
    declared = collect_declarations(REPO_ROOT, IGNORED_FOLDERS)
    imports = parse_imports_with_filter(REPO_ROOT, IGNORED_FOLDERS)
    return declared, imports


def test_oraculo_nao_declara_altair() -> None:
    """`altair` não é declarado: ninguém o importa e o `<5` não prendia nada (ADR-0005)."""
    content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    result = parse_pyproject(content)

    assert "altair" not in {dep["package"] for dep in result}


def test_nenhum_import_raiz_e_fantasma(
    auditoria: tuple[list[dict[str, str]], list[dict[str, str]]],
) -> None:
    """Todo Import Raiz do repositório é coberto por alguma Declaração.

    O ORÁCULO reprovava na própria auditoria com dois Fantasmas de causas opostas
    (issue #28): `yaml` faltava na Declaração, e `toml` só era importado por um
    fallback que o `requires-python = ">=3.11"` tornava inalcançável.
    """
    declared, imports = auditoria

    ghosts = sorted(ghost["package"] for ghost in analyze_ghost_dependencies(declared, imports))

    assert ghosts == []


def test_nenhuma_dependencia_de_producao_e_zumbi(
    auditoria: tuple[list[dict[str, str]], list[dict[str, str]]],
) -> None:
    """Toda Dependência de Produção do repositório é importada por algum módulo.

    O ORÁCULO reprovava na própria auditoria com `pandas` declarado e nunca
    importado (issue #32): quem o exigia era o `streamlit`, como transitiva.
    A guarda não gera falso positivo porque `zombie_analizer` pula tudo que tem
    `Origem == Desenvolvimento` (ADR-0003) — é só essa checagem que isenta o
    `pytest`. Viver na Exclusão faz o contrário: tira os imports de `tests/` da
    comparação, e é justamente o que tornaria o `pytest` Zumbi se a checagem de
    Origem não existisse.
    """
    declared, imports = auditoria

    zombies = sorted(zombie["package"] for zombie in analyze_zombie_dependencies(declared, imports))

    assert zombies == []
