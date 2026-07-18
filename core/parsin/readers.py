"""
Módulo responsável pela leitura e parsing de arquivos de configuração de dependências.

Realiza o carregamento e a extração de dados brutos de arquivos como:
- requirements.txt (padrão pip)
- pyproject.toml  (PEP 621 e Poetry)
- environment.yml (Conda)
- *.lock          (uv.lock, poetry.lock — formato TOML)

Entrada:
- Conteúdo do arquivo de configuração (string)

Saída:
- Lista de dicionários contendo 'Pacote', 'Versão Usada' e 'Origem'
"""

import re
from typing import Dict, List, Optional
from utils.constants import ORIGIN_DEVELOPMENT, ORIGIN_PRODUCTION
from utils.functions import READERS, registrar

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

try:
    import yaml
except ImportError:
    yaml = None


def parse_dependency_string(line: str) -> Optional[Dict[str, str]]:
    """
    Analisa uma linha de texto e retorna nome e Versão Usada da dependência.

    Só um pin exato determina a Versão Usada; um especificador de faixa não fixa
    versão nenhuma e devolve "" (ADR-0002). Sem isso, `!=1.25.0,>=1.21.1` cairia
    na armadilha de reportar a versão *excluída* como usada.

    Trata os seguintes casos do PEP 508 e formatos comuns:
    - Pin exato:                 requests==2.31.0                  → requests | 2.31.0
    - Marcadores de ambiente: numpy>=1.26; python_version < '3.14'  → numpy | ""
    - Extras entre colchetes: requests[security]>=2.28              → requests | ""
    - Múltiplos especificadores: urllib3!=1.25.0,>=1.21.1           → urllib3 | ""
    - Apenas nome sem versão:    Pillow                             → pillow | ""
    - Dependência condicional sem versão: tzdata; sys_platform==... → tzdata | ""

    Args:
        line: Linha de texto com a declaração da dependência.

    Returns:
        Dict com 'Pacote' e 'Versão Usada', ou None se a linha for inválida.
    """
    line = line.split("#")[0].strip()
    if not line:
        return None

    line = line.split(";")[0].strip()

    line = re.sub(r"\[.*?\]", "", line).strip()

    if not line:
        return None

    match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", line)
    if not match:
        return None

    name = match.group(1).strip().lower()
    version_raw = match.group(2).strip()

    # Só um pin exato (== do PEP 508, === do PEP 440) fixa a Versão Usada; um
    # especificador de faixa (>=, <, !=, ^, ~=) não determina versão (ADR-0002).
    pin_match = re.match(r"={2,3}\s*(\d[^\s,;]*)", version_raw)
    version = pin_match.group(1) if pin_match else ""

    return {"Pacote": name, "Versão Usada": version}


def _clean_conda_dep(dep_string: str) -> Optional[Dict[str, str]]:
    """
    Analisa uma entrada de dependência do Conda (environment.yml).

    Conda usa formatos como: 'numpy', 'numpy=1.24', 'numpy>=1.24'.
    Ignora entradas com ':' (canal específico como 'conda-forge::numpy').

    Args:
        dep_string: String da dependência conda.

    Returns:
        Dict com 'Pacote' e 'Versão Usada', ou None se inválida.
    """
    dep_string = str(dep_string).strip()

    if "::" in dep_string:
        dep_string = dep_string.split("::")[-1]

    dep_string = re.sub(r"(?<![=<>!])=(?!=)", "==", dep_string)

    return parse_dependency_string(dep_string)


def _parse_dependency_list(entries: List[str], origin: str) -> List[Dict[str, str]]:
    """
    Analisa uma lista de declarações PEP 508 e carimba a Origem de cada uma.

    Ignora 'python', que é o interpretador e não um pacote do PyPI.

    Args:
        entries: Linhas de declaração (ex: ["requests>=2.33.0"]).
        origin: Origem a atribuir a cada pacote da lista.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Usada' e 'Origem'.
    """
    if not isinstance(entries, list):
        return []

    dependencies = []
    for entry in entries:
        result = parse_dependency_string(str(entry))
        if result and result["Pacote"] != "python":
            result["Origem"] = origin
            dependencies.append(result)
    return dependencies


def _as_dict(value: object) -> Dict[str, object]:
    """Retorna value se for uma tabela; caso contrário, uma tabela vazia.

    Um pyproject.toml de Projeto-Alvo arbitrário pode ser malformado (ex.:
    [tool.poetry.group] declarado como string). Normalizar cada seção para
    dict antes de varrer evita AttributeError e degrada de forma limpa.

    Args:
        value: Valor lido do TOML, de tipo desconhecido.

    Returns:
        O próprio value quando for dict; senão, um dict vazio.
    """
    return value if isinstance(value, dict) else {}


def _parse_dependency_table(table: Dict[str, object], origin: str) -> List[Dict[str, str]]:
    """
    Analisa uma tabela de dependências do Poetry e carimba a Origem de cada uma.

    O Poetry declara dependências como pares nome/especificador, onde o
    especificador pode ser uma string ("^2.33.0") ou uma tabela com a versão
    e opções extras ({version = "^2.33.0", extras = ["security"]}).

    Args:
        table: Tabela nome → especificador de versão.
        origin: Origem a atribuir a cada pacote da tabela.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Usada' e 'Origem'.
    """
    if not isinstance(table, dict):
        return []

    entries = []
    for name, spec in table.items():
        if isinstance(spec, dict):
            spec = spec.get("version", "")
        entries.append(f"{name}{spec}")
    return _parse_dependency_list(entries, origin)


def _parse_requirements_content(content: str, origin: str) -> List[Dict[str, str]]:
    """
    Lê o conteúdo de um requirements e carimba a Origem de cada dependência.

    Suporta linhas com e sem versão, ignora comentários e linhas
    de opções do pip (ex: -r, --index-url).

    Args:
        content: Conteúdo completo do arquivo como string.
        origin: Origem a atribuir a cada pacote declarado.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Usada' e 'Origem'.
    """
    lines = [line.strip() for line in content.split("\n")]
    return _parse_dependency_list(
        [line for line in lines if not line.startswith("-")], origin
    )


@registrar(READERS, "requirements.txt")
def parse_requirements(content: str) -> List[Dict[str, str]]:
    """
    Lê um requirements.txt, cujas dependências são de Produção.

    Args:
        content: Conteúdo completo do arquivo como string.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Usada' e 'Origem'.
    """
    return _parse_requirements_content(content, ORIGIN_PRODUCTION)


@registrar(READERS, "requirements-dev.txt")
def parse_requirements_dev(content: str) -> List[Dict[str, str]]:
    """
    Lê um requirements-dev.txt, cujas dependências são de Desenvolvimento.

    Precisa de registro próprio: 'requirements-dev.txt' não termina em
    'requirements.txt', então nunca casaria com o reader de Produção.

    Args:
        content: Conteúdo completo do arquivo como string.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Usada' e 'Origem'.
    """
    return _parse_requirements_content(content, ORIGIN_DEVELOPMENT)


@registrar(READERS, "environment.yml")
def parse_environment_yml(content: str) -> List[Dict[str, str]]:
    """
    Lê um environment.yml (Conda) e extrai suas dependências.

    Suporta dois tipos de entrada na lista 'dependencies':
    - String simples: "numpy=1.24.0" ou "numpy>=1.24"
    - Dict com 'pip': lista de pacotes pip dentro do ambiente conda

    Ignora entradas que não são pacotes Python (ex: "python=3.11").

    O environment.yml descreve o ambiente de execução do Projeto-Alvo, então
    seus pacotes são Dependências de Produção.

    Args:
        content: Conteúdo completo do arquivo como string.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Usada' e 'Origem'.
    """
    if yaml is None:
        return []

    dependencies = []

    try:
        data = yaml.safe_load(content)
    except Exception:
        return []

    if not isinstance(data, dict):
        return []

    for entry in data.get("dependencies", []):

        if isinstance(entry, str):
            if entry.strip().lower().startswith("python"):
                continue
            result = _clean_conda_dep(entry)
            if result:
                result["Origem"] = ORIGIN_PRODUCTION
                dependencies.append(result)
            continue

        if isinstance(entry, dict) and "pip" in entry:
            dependencies += _parse_dependency_list(
                entry.get("pip", []), ORIGIN_PRODUCTION
            )

    return dependencies


@registrar(READERS, "pyproject.toml")
def parse_pyproject(content: str) -> List[Dict[str, str]]:
    """
    Lê um pyproject.toml (PEP 621 e Poetry) e extrai suas dependências.

    Preserva a Origem de cada pacote:
    - [project].dependencies e [tool.poetry].dependencies → Produção
    - [dependency-groups] e [project.optional-dependencies] → Desenvolvimento
    - [tool.poetry.group.<nome>.dependencies] → Desenvolvimento, qualquer que
      seja o nome do grupo

    Args:
        content: Conteúdo completo do arquivo como string.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Usada' e 'Origem'.
    """
    if tomllib is None:
        return []

    try:
        data = tomllib.loads(content)
    except Exception:
        return []

    if not isinstance(data, dict):
        return []

    project = _as_dict(data.get("project"))

    dependencies = _parse_dependency_list(
        project.get("dependencies", []), ORIGIN_PRODUCTION
    )

    for extra in _as_dict(project.get("optional-dependencies")).values():
        dependencies += _parse_dependency_list(extra, ORIGIN_DEVELOPMENT)

    for group in _as_dict(data.get("dependency-groups")).values():
        dependencies += _parse_dependency_list(group, ORIGIN_DEVELOPMENT)

    poetry = _as_dict(_as_dict(data.get("tool")).get("poetry"))
    dependencies += _parse_dependency_table(
        poetry.get("dependencies", {}), ORIGIN_PRODUCTION
    )

    for group in _as_dict(poetry.get("group")).values():
        dependencies += _parse_dependency_table(
            _as_dict(group).get("dependencies", {}), ORIGIN_DEVELOPMENT
        )

    return dependencies


@registrar(READERS, ".lock")
def parse_lock(content: str) -> List[Dict[str, str]]:
    """
    Lê arquivos *.lock no formato TOML (uv.lock, poetry.lock).

    Ambos os gerenciadores armazenam pacotes em uma lista 'package'
    com os campos 'name' e 'version'.

    O Lock resolve versões, não define o conjunto auditado (ADR-0002): ele não
    separa produção de desenvolvimento, então seus pacotes ficam como Produção.

    Args:
        content: Conteúdo completo do arquivo como string.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Usada' e 'Origem'.
    """
    if tomllib is None:
        return []

    dependencies = []

    try:
        data = tomllib.loads(content)
    except Exception:
        return []

    for package in data.get("package", []):
        name = package.get("name")
        version = package.get("version", "")
        if name and name.lower() != "python":
            dependencies.append(
                {
                    "Pacote": name.lower(),
                    "Versão Usada": version if version else "",
                    "Origem": ORIGIN_PRODUCTION,
                }
            )

    return dependencies
