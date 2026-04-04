"""
Módulo responsável pela comunicação com a API do PyPI.

Realiza consultas para obter informações sobre pacotes, como:
- Versão mais recente
- Metadados
- Histórico de releases

Entrada:
- Nome do pacote

Saída:
- Dados retornados pela API do PyPI
"""

import requests
from requests.exceptions import RequestException
from typing import Optional
from core.constants import PYPI_BASE_URL


def get_latest_version(package_name: str) -> Optional[str]:
    """
    Consulta a API do PyPI e retorna a versão mais recente de um pacote.

    Args:
        package_name (str): O nome padronizado do pacote (ex: 'pandas').

    Returns:
        Optional[str]: A string da versão mais recente (ex: '2.1.0') se o pacote
                       for encontrado e a requisição for bem-sucedida.
                       Retorna None se o pacote não existir ou se houver um erro de rede.
    """
    if not package_name:
        return None

    url = f"{PYPI_BASE_URL}/{package_name}/json"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            return data.get("info", {}).get("version")

        return None

    except RequestException:
        return None
