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
- Lista de dicionários contendo 'Pacote', 'Versão Atual' e 'Origem'
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
    Analisa uma linha de texto e retorna nome e versão da dependência.

    Trata os seguintes casos do PEP 508 e formatos comuns:
    - Marcadores de ambiente: numpy>=1.26; python_version < '3.14'  → numpy | 1.26
    - Extras entre colchetes: requests[security]>=2.28              → requests | 2.28
    - Múltiplos especificadores: urllib3!=1.25.0,>=1.21.1           → urllib3 | 1.25.0
    - Apenas nome sem versão:    Pillow                             → pillow | ""
    - Dependência condicional sem versão: tzdata; sys_platform==... → tzdata | ""

    Args:
        line: Linha de texto com a declaração da dependência.

    Returns:
        Dict com 'Pacote' e 'Versão Atual', ou None se a linha for inválida.
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
    version_match = re.search(r"(\d+[\d\.]*)", version_raw)
    version = version_match.group(1) if version_match else ""

    return {"Pacote": name, "Versão Atual": version}


def _clean_conda_dep(dep_string: str) -> Optional[Dict[str, str]]:
    """
    Analisa uma entrada de dependência do Conda (environment.yml).

    Conda usa formatos como: 'numpy', 'numpy=1.24', 'numpy>=1.24'.
    Ignora entradas com ':' (canal específico como 'conda-forge::numpy').

    Args:
        dep_string: String da dependência conda.

    Returns:
        Dict com 'Pacote' e 'Versão Atual', ou None se inválida.
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
        Lista de dicts com 'Pacote', 'Versão Atual' e 'Origem'.
    """
    dependencies = []
    for entry in entries:
        result = parse_dependency_string(str(entry))
        if result and result["Pacote"] != "python":
            result["Origem"] = origin
            dependencies.append(result)
    return dependencies


def _parse_requirements_content(content: str, origin: str) -> List[Dict[str, str]]:
    """
    Lê o conteúdo de um requirements e carimba a Origem de cada dependência.

    Suporta linhas com e sem versão, ignora comentários e linhas
    de opções do pip (ex: -r, --index-url).

    Args:
        content: Conteúdo completo do arquivo como string.
        origin: Origem a atribuir a cada pacote declarado.

    Returns:
        Lista de dicts com 'Pacote', 'Versão Atual' e 'Origem'.
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
        Lista de dicts com 'Pacote', 'Versão Atual' e 'Origem'.
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
        Lista de dicts com 'Pacote', 'Versão Atual' e 'Origem'.
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
        Lista de dicts com 'Pacote', 'Versão Atual' e 'Origem'.
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
        Lista de dicts com 'Pacote', 'Versão Atual' e 'Origem'.
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
                    "Versão Atual": version if version else "",
                    "Origem": ORIGIN_PRODUCTION,
                }
            )

    return dependencies
