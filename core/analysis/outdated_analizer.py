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
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.pypi.pypi_client import get_latest_version
from packaging.version import parse as parse_version
from utils.constants import VERSION_UNAVAILABLE


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


def _checar_dependencia(dep: dict) -> dict:
    """
    Consulta o PyPI para uma única dependência e preenche os campos
    'Versão PyPI' e 'Status' diretamente no dicionário.

    Chamada em paralelo pelo ThreadPoolExecutor.

    Args:
        dep: Dicionário com pelo menos 'Pacote' e 'Versão Usada'.

    Returns:
        O mesmo dicionário com 'Versão PyPI' e 'Status' preenchidos.
    """
    pypi_version    = get_latest_version(dep["Pacote"])
    versao_usada_raw = dep["Versão Usada"].strip() if dep["Versão Usada"] else ""
    versao_usada    = _extract_version_number(versao_usada_raw)

    if pypi_version is None:
        dep["Versão PyPI"] = "N/A"
        dep["Status"]      = "Desconhecido"
    else:
        dep["Versão PyPI"] = pypi_version

        if not versao_usada:
            # Sem Lock e sem pin, a Versão Usada é desconhecida: não se afirma
            # "Atualizado" nem se copia a versão do PyPI (ADR-0002).
            dep["Versão Usada"] = VERSION_UNAVAILABLE
            dep["Status"]       = VERSION_UNAVAILABLE
        else:
            try:
                if parse_version(versao_usada) < parse_version(pypi_version):
                    dep["Status"] = "Desatualizado"
                else:
                    dep["Status"] = "Atualizado"
            except Exception:
                dep["Status"] = "Versão Inválida"

    return dep


def analyze_dependency_status(dependencies: list[dict]) -> list[dict]:
    """
    Analisa o status de cada dependência comparando com o PyPI.

    Utiliza ThreadPoolExecutor para disparar as requisições em paralelo,
    reduzindo o tempo de execução de O(n) sequencial para próximo de O(1)
    em relação ao número de dependências.

    Args:
        dependencies: Lista de dicts com 'Pacote' e 'Versão Usada'.

    Returns:
        A mesma lista com 'Versão PyPI' e 'Status' preenchidos em cada item.
    """
    if not dependencies:
        return []

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(_checar_dependencia, dep): dep for dep in dependencies}

        for future in as_completed(futures):
            future.result()

    return dependencies