import pytest

from core.parsin.readers import (
    parse_dependency_string,
    parse_environment_yml,
    parse_lock,
    parse_pyproject,
    parse_requirements,
    parse_requirements_dev,
)
from utils.functions import READERS


def test_pin_exato_define_versao_usada():
    """Um pin exato (==X.Y.Z) determina a Versão Usada."""
    assert parse_dependency_string("requests==2.31.0") == {
        "package": "requests",
        "Versão Usada": "2.31.0",
    }


@pytest.mark.parametrize(
    "line",
    [
        "altair<5",
        "numpy>=1.26",
        "urllib3!=1.25.0,>=1.21.1",
        "requests^2.33.0",
        "Pillow",
    ],
)
def test_especificador_nao_pinado_nao_define_versao_usada(line):
    """Sem pin exato, o especificador não determina Versão Usada (ADR-0002)."""
    result = parse_dependency_string(line)

    assert result["Versão Usada"] == ""


def test_versao_excluida_nao_vira_versao_usada():
    """`!=1.25.0,>=1.21.1` não devolve a versão excluída (1.25.0) como usada."""
    result = parse_dependency_string("urllib3!=1.25.0,>=1.21.1")

    assert result == {"package": "urllib3", "Versão Usada": ""}


def test_pep621_dependencies_tem_origem_de_producao():
    """[project].dependencies são Dependências de Produção."""
    content = """
[project]
name = "alvo"
dependencies = ["requests>=2.33.0", "pandas>=3.0.1"]
"""

    result = parse_pyproject(content)

    assert result == [
        {"package": "requests", "Versão Usada": "", "Origem": "Production"},
        {"package": "pandas", "Versão Usada": "", "Origem": "Production"},
    ]


def test_pyproject_do_proprio_oraculo_e_lido():
    """Um Projeto-Alvo com a forma do ORÁCULO é lido com a Origem correta.

    Snapshot fixo, não o pyproject.toml vivo do repositório: a Origem que o reader
    devolve não pode depender de o ORÁCULO trocar de dependência (issue #21).
    """
    content = """
[project]
name = "alvo"
requires-python = ">=3.11"
dependencies = [
    "pandas>=3.0.1",
    "streamlit>=1.37.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
"""

    result = parse_pyproject(content)

    origens = {dep["package"]: dep["Origem"] for dep in result}
    assert origens == {
        "pandas": "Production",
        "streamlit": "Production",
        "pytest": "Development",
    }


def test_pyproject_esta_registrado_como_reader():
    """O registry precisa reconhecer pyproject.toml para o pipeline achá-lo."""
    assert READERS["pyproject.toml"] is parse_pyproject


def test_requirements_txt_tem_origem_de_producao():
    """requirements.txt declara Dependências de Produção."""
    result = parse_requirements("requests>=2.33.0\npandas>=3.0.1\n")

    assert [dep["Origem"] for dep in result] == ["Production", "Production"]


def test_requirements_dev_txt_tem_origem_de_desenvolvimento():
    """requirements-dev.txt declara Dependências de Desenvolvimento (ADR-0003)."""
    result = parse_requirements_dev("pytest>=8.0.0\nruff>=0.6.0\n")

    assert [dep["Origem"] for dep in result] == ["Development", "Development"]


def test_requirements_dev_tem_reader_proprio_no_registry():
    """requirements-dev.txt não casa com a chave 'requirements.txt' por endswith."""
    assert READERS["requirements-dev.txt"] is parse_requirements_dev


def test_environment_yml_tem_origem():
    """environment.yml declara o ambiente de execução: Origem de Produção."""
    content = """
name: alvo
dependencies:
  - python=3.11
  - numpy=1.24.0
  - pip:
    - requests>=2.33.0
"""

    result = parse_environment_yml(content)

    assert [(dep["package"], dep["Origem"]) for dep in result] == [
        ("numpy", "Production"),
        ("requests", "Production"),
    ]


def test_environment_yml_com_dependencies_vazio_nao_quebra() -> None:
    """`dependencies:` sem itens devolve lista vazia, não TypeError.

    O YAML resolve a chave presente e vazia para None, e não para lista: o
    `.get("dependencies", [])` não protege, porque a chave existe. Um Projeto-Alvo
    com essa Declaração abortaria a análise inteira.
    """
    content = """
name: alvo
dependencies:
"""

    assert parse_environment_yml(content) == []


def test_lock_tem_origem():
    """O Lock resolve versões; seus pacotes recebem Origem de Produção."""
    content = """
[[package]]
name = "requests"
version = "2.33.0"
"""

    result = parse_lock(content)

    assert result == [
        {"package": "requests", "Versão Usada": "2.33.0", "Origem": "Production"},
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

    assert [dep["package"] for dep in result] == ["requests"]


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

    origens = {dep["package"]: dep["Origem"] for dep in result}
    assert origens == {
        "streamlit": "Production",
        "pytest": "Development",
        "ruff": "Development",
        "mkdocs": "Development",
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

    origens = {dep["package"]: dep["Origem"] for dep in result}
    assert origens == {
        "requests": "Production",
        "pytest": "Development",
        "mypy": "Development",
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
        {"package": "requests", "Versão Usada": "", "Origem": "Production"},
        {"package": "pandas", "Versão Usada": "", "Origem": "Production"},
    ]


def test_pin_exato_do_poetry_define_a_versao_usada():
    """No Poetry, `requests = "2.33.0"` (sem operador) é pin exato (#11 AC2).

    Sem tratar o especificador nu, o nome absorvia a versão ("requests2.33.0") e
    o pin — única fonte de Versão Usada fora do Lock — se perdia.
    """
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.dependencies]
requests = "2.33.0"
"""

    result = parse_pyproject(content)

    assert result == [
        {"package": "requests", "Versão Usada": "2.33.0", "Origem": "Production"},
    ]


def test_pin_exato_do_poetry_em_tabela_define_a_versao_usada():
    """O pin nu também vale quando a dependência vem como tabela com extras."""
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.dependencies]
requests = { version = "2.33.0", extras = ["security"] }
"""

    result = parse_pyproject(content)

    assert result == [
        {"package": "requests", "Versão Usada": "2.33.0", "Origem": "Production"},
    ]


def test_curinga_do_poetry_nao_define_versao_usada():
    """`*` aceita qualquer versão, logo não fixa Versão Usada (ADR-0002)."""
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.dependencies]
requests = "*"
"""

    result = parse_pyproject(content)

    assert result == [
        {"package": "requests", "Versão Usada": "", "Origem": "Production"},
    ]


def test_grupo_dev_do_poetry_tem_origem_de_desenvolvimento():
    """[tool.poetry.group.dev.dependencies] são de Desenvolvimento (ADR-0003)."""
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
ruff = "^0.6.0"
"""

    result = parse_pyproject(content)

    assert result == [
        {"package": "pytest", "Versão Usada": "", "Origem": "Development"},
        {"package": "ruff", "Versão Usada": "", "Origem": "Development"},
    ]


def test_python_nao_e_tratado_como_pacote_dentro_de_grupo_poetry():
    """'python' segue sendo o interpretador, também dentro de um grupo."""
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.group.dev.dependencies]
python = "^3.11"
pytest = "^8.0.0"
"""

    result = parse_pyproject(content)

    assert [dep["package"] for dep in result] == ["pytest"]


def test_group_do_poetry_com_valor_nao_tabela_nao_derruba_pipeline():
    """[tool.poetry.group] com valor não-tabela degrada sem exceção (issue #19)."""
    content = """
[tool.poetry]
name = "alvo"
group = "dev"

[tool.poetry.dependencies]
requests = "^2.33.0"
"""

    result = parse_pyproject(content)

    assert result == [
        {"package": "requests", "Versão Usada": "", "Origem": "Production"},
    ]


def test_grupo_poetry_com_dependencies_nao_tabela_e_ignorado_sem_quebrar_os_demais():
    """Um grupo com 'dependencies' não-tabela é ignorado; os demais sobrevivem."""
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.dependencies]
requests = "^2.33.0"

[tool.poetry.group.dev]
dependencies = "pytest"

[tool.poetry.group.lint.dependencies]
mypy = "^1.11.0"
"""

    result = parse_pyproject(content)

    origens = {dep["package"]: dep["Origem"] for dep in result}
    assert origens == {
        "requests": "Production",
        "mypy": "Development",
    }


@pytest.mark.parametrize(
    "content",
    [
        'project = "alvo"\n',
        '[project]\nname = "alvo"\noptional-dependencies = "dev"\n',
        'dependency-groups = "dev"\n[project]\nname = "alvo"\n',
        'tool = "poetry"\n',
    ],
)
def test_secoes_malformadas_degradam_sem_excecao(content):
    """Seções não-tabela (project, tool e os laços dev) não derrubam o pipeline."""
    result = parse_pyproject(content)

    assert isinstance(result, list)


def test_dependency_group_com_valor_string_e_tratado_como_vazio():
    """Um grupo cujo valor é string vira vazio, sem gerar pacotes de um caractere."""
    content = """
[project]
name = "alvo"
dependencies = ["requests>=2.33.0"]

[dependency-groups]
dev = "pytest"
"""

    result = parse_pyproject(content)

    assert result == [
        {"package": "requests", "Versão Usada": "", "Origem": "Production"},
    ]


def test_grupo_poetry_de_nome_arbitrario_convive_com_producao():
    """Qualquer [tool.poetry.group.<nome>] é Desenvolvimento; produção não muda."""
    content = """
[tool.poetry]
name = "alvo"

[tool.poetry.dependencies]
requests = "^2.33.0"

[tool.poetry.group.lint.dependencies]
mypy = "^1.11.0"

[tool.poetry.group.docs.dependencies]
mkdocs = "^1.6.0"
"""

    result = parse_pyproject(content)

    origens = {dep["package"]: dep["Origem"] for dep in result}
    assert origens == {
        "requests": "Production",
        "mypy": "Development",
        "mkdocs": "Development",
    }
