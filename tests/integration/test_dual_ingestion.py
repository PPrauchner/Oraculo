"""
Garante que os dois modos de ingestão (ADR-0001) auditam o mesmo Projeto-Alvo.

Um Projeto-Alvo em diretório precisa produzir exatamente o mesmo relatório que o
mesmo projeto compactado. As divergências plausíveis entre os dois modos estão
todas exercitadas aqui: pasta-embrulho do archive, ordem dos arquivos, pastas de
ambiente que só existem em disco e fim de linha do Windows.
"""

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from core.ingestion.filter import get_unique_folders, validate_project_structure
from core.parsin.declaration_collector import collect_declarations
from core.parsin.import_parser import parse_imports
from core.parsin.lock_resolver import build_lock_version_map, resolve_used_versions

PROJECT_FILES = {
    "pyproject.toml": (
        "[project]\n"
        'name = "alvo"\n'
        'dependencies = ["requests>=2.0", "pandas>=3.0", "plotly>=6.0"]\n'
        "\n"
        "[dependency-groups]\n"
        'dev = ["pytest>=8.0"]\n'
    ),
    "uv.lock": (
        "version = 1\n"
        "\n"
        "[[package]]\n"
        'name = "requests"\n'
        'version = "2.33.0"\n'
        "\n"
        "[[package]]\n"
        'name = "pandas"\n'
        'version = "3.0.1"\n'
    ),
    "main.py": "import requests\nfrom core.service import run\n",
    "core/__init__.py": "",
    "core/service.py": "import pandas\nimport yaml\n",
    "core/helpers/__init__.py": "",
    "core/helpers/dates.py": "import os\nimport plotly\n",
    "tests/test_service.py": "import pytest\nimport responses\n",
    "docs/adr/0001.md": "# decisao\n",
}

# Só existem no diretório em disco; o archive não as carrega
ENVIRONMENT_FILES = {
    ".venv/Lib/site-packages/boto3/__init__.py": "import botocore\n",
    "__pycache__/main.cpython-311.pyc": "",
    ".git/config": "[core]\n",
}


@pytest.fixture
def project_directory(tmp_path: Path) -> Path:
    """Materializa o Projeto-Alvo em disco, com o lixo de ambiente ao redor."""
    root = tmp_path / "meu-projeto"

    for path, content in {**PROJECT_FILES, **ENVIRONMENT_FILES}.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return root


@pytest.fixture
def project_zip() -> zipfile.ZipFile:
    """Compacta o mesmo Projeto-Alvo como o "Download ZIP" do GitHub faria."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zf:
        # Ordem invertida de proposito: a ingestao nao pode depender dela
        for path, content in reversed(list(PROJECT_FILES.items())):
            zf.writestr(f"meu-projeto-main/{path}", content)

    return zipfile.ZipFile(buffer)


@pytest.fixture
def project_tar() -> tarfile.TarFile:
    """O mesmo Projeto-Alvo em TAR, sem pasta-embrulho."""
    buffer = io.BytesIO()

    with tarfile.open(fileobj=buffer, mode="w") as tf:
        for path, content in PROJECT_FILES.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=f"./{path}")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))

    buffer.seek(0)
    return tarfile.open(fileobj=buffer, mode="r")


def _audit(source, ignore_folders: list[str]) -> dict:
    """Roda o pipeline de auditoria e devolve o que o relatório consumiria."""
    declared = collect_declarations(source, ignore_folders)
    declared = resolve_used_versions(
        declared, build_lock_version_map(source, ignore_folders)
    )

    return {
        "declared": declared,
        "imports": parse_imports(source, ignore_folders),
        "folders": get_unique_folders(source),
        "valid": validate_project_structure(source, ignore_folders),
    }


def test_directory_and_zip_produce_identical_reports(project_directory, project_zip):
    """AC #3: mesmo Projeto-Alvo, dois modos de ingestão, relatórios idênticos."""
    assert _audit(project_directory, []) == _audit(project_zip, [])


def test_directory_and_tar_produce_identical_reports(project_directory, project_tar):
    assert _audit(project_directory, []) == _audit(project_tar, [])


def test_the_two_modes_stay_identical_under_exclusions(project_directory, project_zip):
    """A Exclusão precisa valer igual nos dois modos, inclusive com embrulho."""
    assert _audit(project_directory, ["tests", "docs"]) == _audit(
        project_zip, ["tests", "docs"]
    )


def test_the_environment_folders_of_the_directory_are_not_audited(project_directory):
    """`.venv` está em disco mas não é o Projeto-Alvo: não gera Import Raiz."""
    packages = {item["package"] for item in parse_imports(project_directory, [])}

    assert "botocore" not in packages


def test_the_exclusion_reaches_a_wrapped_archive(project_zip):
    """Issue #26: com pasta-embrulho, marcar `tests` exclui de verdade."""
    packages = {item["package"] for item in parse_imports(project_zip, ["tests"])}

    assert "responses" not in packages


def test_the_audit_finds_what_it_should_in_both_modes(project_directory, project_zip):
    """Guarda contra os dois modos concordarem por estarem ambos vazios."""
    for source in (project_directory, project_zip):
        report = _audit(source, ["tests", "docs"])

        declared = {dep["package"] for dep in report["declared"]}
        packages = {item["package"] for item in report["imports"]}

        assert declared == {"requests", "pandas", "plotly", "pytest"}
        # `core` é Módulo Próprio e `os` é stdlib: nenhum dos dois é Import Raiz
        assert packages == {"requests", "pandas", "plotly", "yaml"}
        assert report["valid"] == (True, None)
        assert report["folders"] == ["adr", "core", "docs", "helpers", "tests"]


def test_the_used_version_comes_from_the_lock_in_both_modes(
    project_directory, project_zip
):
    for source in (project_directory, project_zip):
        versions = {
            dep["package"]: dep["used_version"] for dep in _audit(source, [])["declared"]
        }

        assert versions["requests"] == "2.33.0"
        assert versions["pandas"] == "3.0.1"
