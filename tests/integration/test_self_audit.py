"""
O Baita Auditor auditado por ele mesmo: ele é um Projeto-Alvo válido.

Aqui — e só aqui — ler o `pyproject.toml` vivo do repositório é o ponto, não um
descuido. Um teste de unidade de reader não pode depender do que o repositório
declara hoje (issue #21); um teste de auto-auditoria só existe porque depende.

Responsabilidades:
- Guardar as decisões que a própria Declaração do repositório precisa respeitar.
"""

from pathlib import Path

from core.parsin.readers import parse_pyproject

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_baita_auditor_nao_declara_altair():
    """`altair` não é declarado: ninguém o importa e o `<5` não prendia nada (ADR-0005)."""
    content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    result = parse_pyproject(content)

    assert "altair" not in {dep["Pacote"] for dep in result}
