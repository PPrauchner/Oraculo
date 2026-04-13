"""
Módulo responsável pela leitura e parsing de arquivos de configuração de dependências.

Realiza o carregamento e a extração de dados brutos de arquivos como:
- requirements.txt (padrão pip)
- *.lock (gerenciadores de pacotes: uv, Poetry, PDM, etc.)

Entrada:
- Caminho do arquivo de configuração (file_path)

Saída:
- Lista de dicionários contendo 'name' e 'version' das dependências encontradas
"""

import re
from typing import Dict, List, Optional

from utils.functions import READERS, registrar

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None


def parse_dependency_string(line: str) -> Optional[Dict[str, str]]:
    line = line.split("#")[0].strip()
    if not line:
        return None

    match = re.match(r"^([a-zA-Z0-9_\-]+)(.*)$", line)
    if match:
        name = match.group(1).strip().lower()
        version = match.group(2).strip()

        version = re.sub(r"^[^0-9]*", "", version)

        return {"Pacote": name, "Versão Atual": version if version else ""}
    return None


@registrar(READERS, "requirements.txt")
def parse_requirements(content: str) -> List[Dict[str, str]]:
    dependencies = []
    for line in content.split("\n"):
        result = parse_dependency_string(line)
        if result:
            dependencies.append(result)
    return dependencies


@registrar(READERS, ".lock")
def parse_uv_lock(content: str) -> List[Dict[str, str]]:
    if tomllib is None:
        return []

    dependencies = []
    data = tomllib.loads(content)
    packages = data.get("package", [])

    for package in packages:
        name = package.get("name")
        version = package.get("version", "")
        if name and name.lower() != "python":
            dependencies.append(
                {
                    "Pacote": name.lower(),
                    "Versão Atual": version if version else "",
                }
            )

    return dependencies
