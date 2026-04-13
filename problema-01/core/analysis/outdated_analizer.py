"""
Módulo responsável por identificar dependências desatualizadas.

Realiza a comparação entre a versão utilizada no projeto e a versão
mais recente disponível no PyPI.

Entrada:
- Lista de dependências com versões atuais
- Dados obtidos da API do PyPI

Saída:
- Lista de dependências desatualizadas com suas versões
"""

import re
from core.pypi.pypi_client import get_latest_version
from packaging.version import parse as parse_version


def _extract_version_number(version_string: str) -> str:
    """
    Extrai apenas o número de versão de uma string que pode conter especificadores.

    Ex: ">=1.2.3" -> "1.2.3", "==2.0.0" -> "2.0.0", "1.0.0" -> "1.0.0"
    """
    if not version_string:
        return ""

    version_string = version_string.strip()
    match = re.search(r"(\d+\.\d+\.\d+|\d+\.\d+|\d+)", version_string)

    if match:
        return match.group(1)
    return ""


def analyze_dependency_status(dependencies: list[dict]) -> list[dict]:
    """Analisa o status de cada dependência comparando com o PyPI."""
    if dependencies is None:
        return []

    for dep in dependencies:
        pypi_version = get_latest_version(dep["Pacote"])
        versao_atual_raw = dep["Versão Atual"].strip() if dep["Versão Atual"] else ""
        versao_atual = _extract_version_number(versao_atual_raw)

        if versao_atual:
            dep["Versão Atual"] = versao_atual

        if pypi_version is None:
            dep["Versão PyPI"] = "N/A"
            dep["Status"] = "Desconhecido"
        else:
            dep["Versão PyPI"] = pypi_version

            if not versao_atual:
                dep["Versão Atual"] = pypi_version
                dep["Status"] = "Atualizado"
            else:
                try:
                    if parse_version(versao_atual) < parse_version(pypi_version):
                        dep["Status"] = "Desatualizado"
                    else:
                        dep["Status"] = "Atualizado"
                except Exception:
                    dep["Status"] = "Versão Inválida"
    return dependencies
