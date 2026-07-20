"""
Testes do coletor do conjunto auditado.

Garante que o conjunto auditado seja a união das Declarações (ADR-0002):
- o Lock resolve versões, não define o conjunto — nenhuma transitiva entra;
- Declarações repetidas deduplicam por Nome de Distribuição, Origem preservada;
- Declarações dentro de Exclusões ficam de fora.
"""

import io
import zipfile

from core.parsin.declaration_collector import (
    collect_declarations,
    is_lock_filename,
    merge_declarations,
)


def _zip(files: dict[str, str]) -> zipfile.ZipFile:
    """Monta um ZIP em memória a partir de {caminho: conteúdo}."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    buffer.seek(0)
    return zipfile.ZipFile(buffer)


def test_lock_transitives_are_not_audited():
    """Um projeto uv não reporta as transitivas do uv.lock no conjunto auditado."""
    pyproject = """
[project]
name = "alvo"
dependencies = ["requests>=2.31"]
"""
    uv_lock = """
[[package]]
name = "requests"
version = "2.31.0"

[[package]]
name = "certifi"
version = "2024.2.2"

[[package]]
name = "urllib3"
version = "2.2.1"
"""
    archive = _zip({"pyproject.toml": pyproject, "uv.lock": uv_lock})

    audited = collect_declarations(archive, ignore_folders=[])

    names = {dep["Pacote"] for dep in audited}
    assert names == {"requests"}


def test_audited_set_is_union_of_all_declarations():
    """O conjunto auditado une todas as Declarações, com a Origem de cada uma."""
    archive = _zip(
        {
            "requirements.txt": "requests>=2.31\n",
            "requirements-dev.txt": "pytest>=8.0\n",
        }
    )

    audited = collect_declarations(archive, ignore_folders=[])

    origins = {dep["Pacote"]: dep["Origem"] for dep in audited}
    assert origins == {"requests": "Production", "pytest": "Development"}


def test_duplicate_package_deduped_with_first_origin():
    """Pacote declarado duas vezes aparece uma só, com a Origem da primeira."""
    dependencies = [
        {"Pacote": "requests", "Origem": "Production"},
        {"Pacote": "requests", "Origem": "Development"},
        {"Pacote": "pandas", "Origem": "Production"},
    ]

    merged = merge_declarations(dependencies)

    assert merged == [
        {"Pacote": "requests", "Origem": "Production"},
        {"Pacote": "pandas", "Origem": "Production"},
    ]


def test_declarations_inside_exclusions_are_ignored():
    """Uma Declaração dentro de uma Exclusão não entra no conjunto auditado."""
    archive = _zip(
        {
            "requirements.txt": "requests>=2.31\n",
            "tests/requirements.txt": "pytest>=8.0\n",
        }
    )

    audited = collect_declarations(archive, ignore_folders=["tests"])

    names = {dep["Pacote"] for dep in audited}
    assert names == {"requests"}


def test_lock_only_project_produces_empty_set():
    """Um projeto só com Lock e nenhuma Declaração produz conjunto vazio."""
    uv_lock = """
[[package]]
name = "requests"
version = "2.31.0"

[[package]]
name = "certifi"
version = "2024.2.2"
"""
    archive = _zip({"uv.lock": uv_lock})

    assert collect_declarations(archive, ignore_folders=[]) == []


def test_lock_filename_recognizes_locks_not_declarations():
    """is_lock_filename separa Lock de Declaração."""
    assert is_lock_filename("uv.lock")
    assert is_lock_filename("poetry.lock")
    assert is_lock_filename("nested/dir/uv.lock")
    assert not is_lock_filename("requirements.txt")
    assert not is_lock_filename("pyproject.toml")
