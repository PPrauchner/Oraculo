import io
import zipfile

from core.parsin.import_parser import extract_imports_from_code, parse_imports


def _make_zip(files: dict[str, str]) -> zipfile.ZipFile:
    """Monta um archive em memória a partir de um mapa caminho -> conteúdo."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return zipfile.ZipFile(buffer)


def _packages(archive, ignore_folders: list[str] | None = None) -> set[str]:
    """Devolve o conjunto de Imports Raiz encontrados pelo parser."""
    return {item["Pacote"] for item in parse_imports(archive, ignore_folders or [])}


def test_indented_imports_are_detected_as_root_imports():
    """Imports em `try:` e no corpo de função também são Imports Raiz (issue #18)."""
    code = (
        "import requests\n"
        "\n"
        "try:\n"
        "    import yaml\n"
        "except ImportError:\n"
        "    yaml = None\n"
        "\n"
        "def f():\n"
        "    import pandas\n"
    )

    assert extract_imports_from_code(code) == {"requests", "yaml", "pandas"}


def test_indented_imports_are_still_filtered():
    """Filtros valem mesmo indentados: stdlib, Módulo Próprio, underscore, relativo."""
    code = (
        "def f():\n"
        "    import os\n"          # stdlib
        "    import core\n"        # Módulo Próprio
        "    import _internal\n"   # underscore
        "    from . import sibling\n"  # relativo
        "    import requests\n"    # único válido
    )

    assert extract_imports_from_code(code, own_modules={"core"}) == {"requests"}


def test_absolute_import_of_own_module_is_not_a_root_import():
    """Layout plano: `from core.pypi.pypi_client import x` não é Import Raiz."""
    archive = _make_zip(
        {
            "core/__init__.py": "",
            "core/pypi/pypi_client.py": "",
            "pages/loading.py": "from core.pypi.pypi_client import fetch\n",
        }
    )

    assert "core" not in _packages(archive)


def test_external_import_remains_a_root_import():
    """Import externo de verdade continua sendo Import Raiz (vira Fantasma se não declarado)."""
    archive = _make_zip(
        {
            "core/__init__.py": "",
            "core/pypi/pypi_client.py": "import requests\nfrom core.report import x\n",
        }
    )

    assert _packages(archive) == {"requests"}


def test_archive_wrapped_in_project_folder_still_infers_own_modules():
    """Archive que embrulha o projeto numa pasta raiz: o topo é dentro dela."""
    archive = _make_zip(
        {
            "grupo-03/pyproject.toml": "",
            "grupo-03/core/__init__.py": "",
            "grupo-03/pages/__init__.py": "",
            "grupo-03/pages/loading.py": "from core.pypi.pypi_client import x\nimport requests\n",
        }
    )

    assert _packages(archive) == {"requests"}


def test_own_module_wins_over_external_package_with_same_name():
    """Pasta de topo com nome de pacote do PyPI é Módulo Próprio: o layout vence."""
    archive = _make_zip(
        {
            "requests/__init__.py": "",
            "requests/session.py": "",
            "app/__init__.py": "",
            "app/client.py": "import requests\nimport plotly\n",
        }
    )

    assert _packages(archive) == {"plotly"}


def test_top_level_python_file_is_an_own_module():
    """Um `.py` de topo (ex.: main.py) também é Módulo Próprio."""
    archive = _make_zip(
        {
            "main.py": "",
            "core/__init__.py": "",
            "core/runner.py": "import main\nimport requests\n",
        }
    )

    assert _packages(archive) == {"requests"}


def test_src_layout_modules_inside_src_are_own_modules():
    """Layout `src/`: os Módulos Próprios são as pastas dentro de src, não o `src` em si."""
    archive = _make_zip(
        {
            "pyproject.toml": "",
            "src/myapp/__init__.py": "",
            "src/myapp/service.py": "import requests\nfrom myapp.helpers import x\n",
            "src/myapp/helpers.py": "",
        }
    )

    assert _packages(archive) == {"requests"}
