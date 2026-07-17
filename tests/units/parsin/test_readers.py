from pathlib import Path

import pytest

from core.parsin.readers import (
    parse_environment_yml,
    parse_lock,
    parse_pyproject,
    parse_requirements,
    parse_requirements_dev,
)
from utils.functions import READERS


def test_pep621_dependencies_tem_origem_de_producao():
    """[project].dependencies são Dependências de Produção."""
    content = """
[project]
name = "alvo"
dependencies = ["requests>=2.33.0", "pandas>=3.0.1"]
"""

    result = parse_pyproject(content)

    assert result == [
        {"Pacote": "requests", "Versão Atual": "2.33.0", "Origem": "Produção"},
        {"Pacote": "pandas", "Versão Atual": "3.0.1", "Origem": "Produção"},
    ]


def test_pyproject_do_proprio_baita_auditor_e_lido():
    """O Baita Auditor é um Projeto-Alvo válido: seu pyproject.toml é lido."""
    repo_root = Path(__file__).resolve().parents[3]
    content = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    result = parse_pyproject(content)

    origens = {dep["Pacote"]: dep["Origem"] for dep in result}
    assert origens["streamlit"] == "Produção"
    assert origens["pandas"] == "Produção"
    assert origens["pytest"] == "Desenvolvimento"


def test_pyproject_esta_registrado_como_reader():
    """O registry precisa reconhecer pyproject.toml para o pipeline achá-lo."""
    assert READERS["pyproject.toml"] is parse_pyproject


def test_requirements_txt_tem_origem_de_producao():
    """requirements.txt declara Dependências de Produção."""
    result = parse_requirements("requests>=2.33.0\npandas>=3.0.1\n")

    assert [dep["Origem"] for dep in result] == ["Produção", "Produção"]


def test_requirements_dev_txt_tem_origem_de_desenvolvimento():
    """requirements-dev.txt declara Dependências de Desenvolvimento (ADR-0003)."""
    result = parse_requirements_dev("pytest>=8.0.0\nruff>=0.6.0\n")

    assert [dep["Origem"] for dep in result] == ["Desenvolvimento", "Desenvolvimento"]


def test_requirements_dev_tem_reader_proprio_no_registry():
    """requirements-dev.txt não casa com a chave 'requirements.txt' por endswith."""
    assert READERS["requirements-dev.txt"] is parse_requirements_dev


def test_environment_yml_tem_origem():
    """environment.yml declara o ambiente de execução: Origem de Produção."""
    pytest.importorskip("yaml", reason="parse_environment_yml depende de PyYAML")

    content = """
name: alvo
dependencies:
  - python=3.11
  - numpy=1.24.0
  - pip:
    - requests>=2.33.0
"""

    result = parse_environment_yml(content)

    assert [(dep["Pacote"], dep["Origem"]) for dep in result] == [
        ("numpy", "Produção"),
        ("requests", "Produção"),
    ]


def test_lock_tem_origem():
    """O Lock resolve versões; seus pacotes recebem Origem de Produção."""
    content = """
[[package]]
name = "requests"
version = "2.33.0"
"""

    result = parse_lock(content)

    assert result == [
        {"Pacote": "requests", "Versão Atual": "2.33.0", "Origem": "Produção"},
    ]


def test_python_nao_e_tratado_como_pacote():
    """'python' é o interpretador, não um pacote do PyPI."""
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.33.0"
"""

    result = parse_pyproject(content)

    assert [dep["Pacote"] for dep in result] == ["requests"]


def test_dependency_groups_tem_origem_de_desenvolvimento():
    """[dependency-groups] são Dependências de Desenvolvimento (ADR-0003)."""
    content = """
[project]
name = "alvo"
dependencies = ["streamlit>=1.37.0"]

[dependency-groups]
dev = ["pytest>=8.0.0", "ruff>=0.6.0"]
docs = ["mkdocs>=1.6.0"]
"""

    result = parse_pyproject(content)

    origens = {dep["Pacote"]: dep["Origem"] for dep in result}
    assert origens == {
        "streamlit": "Produção",
        "pytest": "Desenvolvimento",
        "ruff": "Desenvolvimento",
        "mkdocs": "Desenvolvimento",
    }


def test_optional_dependencies_tem_origem_de_desenvolvimento():
    """[project.optional-dependencies] são Dependências de Desenvolvimento."""
    content = """
[project]
name = "alvo"
dependencies = ["requests>=2.33.0"]

[project.optional-dependencies]
test = ["pytest>=8.0.0"]
lint = ["mypy>=1.11.0"]
"""

    result = parse_pyproject(content)

    origens = {dep["Pacote"]: dep["Origem"] for dep in result}
    assert origens == {
        "requests": "Produção",
        "pytest": "Desenvolvimento",
        "mypy": "Desenvolvimento",
    }


def test_formato_poetry_tem_origem_de_producao():
    """[tool.poetry.dependencies] são Dependências de Produção."""
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.dependencies]
requests = "^2.33.0"
pandas = ">=3.0.1"
"""

    result = parse_pyproject(content)

    assert result == [
        {"Pacote": "requests", "Versão Atual": "2.33.0", "Origem": "Produção"},
        {"Pacote": "pandas", "Versão Atual": "3.0.1", "Origem": "Produção"},
    ]
