"""
O Baita Auditor auditado por ele mesmo: ele é um Projeto-Alvo válido.

Aqui — e só aqui — ler o `pyproject.toml` vivo do repositório é o ponto, não um
descuido. Um teste de unidade de reader não pode depender do que o repositório
declara hoje (issue #21); um teste de auto-auditoria só existe porque depende.

Responsabilidades:
- Guardar as decisões que a própria Declaração do repositório precisa respeitar.
"""

from pathlib import Path

from core.analysis.ghost_analizer import analyze_ghost_dependencies
from core.parsin.declaration_collector import collect_declarations
from core.parsin.import_parser import parse_imports_with_filter
from core.parsin.readers import parse_pyproject

REPO_ROOT = Path(__file__).resolve().parents[2]

# `tests` é Exclusão: é onde vivem as Dependências de Desenvolvimento (ADR-0003).
IGNORED_FOLDERS = ["tests"]


def test_baita_auditor_nao_declara_altair():
    """`altair` não é declarado: ninguém o importa e o `<5` não prendia nada (ADR-0005)."""
    content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    result = parse_pyproject(content)

    assert "altair" not in {dep["Pacote"] for dep in result}


def test_nenhum_import_raiz_e_fantasma():
    """Todo Import Raiz do repositório é coberto por alguma Declaração.

    O ORÁCULO reprovava na própria auditoria com dois Fantasmas de causas opostas
    (issue #28): `yaml` faltava na Declaração, e `toml` só era importado por um
    fallback que o `requires-python = ">=3.11"` tornava inalcançável.
    """
    declared = collect_declarations(REPO_ROOT, IGNORED_FOLDERS)
    imports = parse_imports_with_filter(REPO_ROOT, IGNORED_FOLDERS)

    ghosts = sorted(ghost["Pacote"] for ghost in analyze_ghost_dependencies(declared, imports))

    assert ghosts == []
