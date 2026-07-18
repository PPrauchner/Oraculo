"""
Testes do cliente do PyPI.

Garantem, sem rede (resposta mockada), que uma única resposta de
`/pypi/NAME/json` fornece os três dados exigidos pelo ADR-0004: versão mais
recente, Tamanho (bytes do wheel, sdist como fallback) e Idade (hoje menos o
`upload_time`) da Versão Usada.
"""

from datetime import date
from unittest.mock import patch

import requests

from core.pypi.pypi_client import (
    fetch_package_data,
    get_latest_version,
    get_release_age_days,
    get_release_size,
)


def _pypi_response(payload: dict):
    """Cria um mock de resposta HTTP com `.json()` e `.raise_for_status()`."""
    response = type("FakeResponse", (), {})()
    response.json = lambda: payload
    response.raise_for_status = lambda: None
    return response


_SAMPLE = {
    "info": {"version": "2.0.0"},
    "releases": {
        "2.0.0": [
            {
                "packagetype": "sdist",
                "size": 500,
                "upload_time": "2024-01-10T00:00:00",
            },
            {
                "packagetype": "bdist_wheel",
                "size": 1200,
                "upload_time": "2024-01-10T00:00:00",
            },
        ],
    },
}


def test_fetch_devolve_tamanho_do_wheel_da_versao():
    """Uma única resposta mockada fornece o Tamanho (bytes do wheel) da versão."""
    with patch(
        "core.pypi.pypi_client.requests.get",
        return_value=_pypi_response(_SAMPLE),
    ):
        data = fetch_package_data("pandas")

    assert get_latest_version(data) == "2.0.0"
    assert get_release_size(data, "2.0.0") == 1200


def test_versao_sem_wheel_usa_o_sdist():
    """Sem wheel, o Tamanho vem do sdist (fallback do ADR-0004)."""
    data = {
        "info": {"version": "1.0.0"},
        "releases": {
            "1.0.0": [
                {"packagetype": "sdist", "size": 777, "upload_time": "2023-05-01T00:00:00"},
            ],
        },
    }

    assert get_release_size(data, "1.0.0") == 777


def test_pacote_ausente_do_pypi_devolve_none():
    """404/rede indisponível não quebra a análise: fetch devolve None."""
    with patch(
        "core.pypi.pypi_client.requests.get",
        side_effect=requests.exceptions.RequestException("404"),
    ):
        assert fetch_package_data("pacote-interno-privado") is None


def test_versao_ausente_nao_tem_tamanho_nem_idade():
    """Versão que não consta em `releases` devolve None (indisponível, não zero)."""
    assert get_release_size(_SAMPLE, "9.9.9") is None
    assert get_release_age_days(_SAMPLE, "9.9.9", today=date(2024, 1, 20)) is None


def test_idade_e_dias_desde_o_upload_da_versao():
    """Idade é hoje menos o upload_time da própria versão (ADR-0004)."""
    age = get_release_age_days(_SAMPLE, "2.0.0", today=date(2024, 1, 20))

    assert age == 10
