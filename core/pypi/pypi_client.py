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
from utils.constants import PYPI_BASE_URL


def get_latest_version(package_name: str) -> str:
    """
    Faz uma requisição à API do PyPI para descobrir a versão mais recente de um pacote.
    Possui tratamento de erros de rede para não travar o sistema.
    """
    url = f"{PYPI_BASE_URL}/{package_name}/json"

    try:
        response = requests.get(url, timeout=5)

        response.raise_for_status()

        data = response.json()
        return data["info"]["version"]

    except requests.exceptions.RequestException as e:
        print(f"Não foi possível checar o pacote '{package_name}' no PyPI. ({e})")
        return None
