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

from core.pypi import pypi_client
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
        "core.pypi.pypi_client._SESSION.get",
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
        "core.pypi.pypi_client._SESSION.get",
        side_effect=requests.exceptions.RequestException("404"),
    ):
        assert fetch_package_data("pacote-interno-privado") is None


def test_requisicoes_passam_por_uma_unica_sessao_compartilhada():
    """Todas as buscas passam pela mesma `Session` do módulo.

    As buscas correm em paralelo (32 threads); uma `Session` compartilhada
    reaproveita conexão e handshake TLS entre elas. Irrelevante para 6 pacotes,
    relevante para 100+.
    """
    assert isinstance(pypi_client._SESSION, requests.Session)

    with patch.object(
        pypi_client._SESSION, "get", return_value=_pypi_response(_SAMPLE)
    ) as session_get:
        fetch_package_data("pandas")
        fetch_package_data("flask")

    assert session_get.call_count == 2


def test_tamanho_nao_depende_da_ordem_dos_wheels_na_resposta():
    """Vários wheels da mesma versão dão sempre o mesmo Tamanho (ADR-0004).

    Um pacote com wheels por plataforma (numpy publica dezenas, com 4x de variação
    de tamanho) não pode mudar de Tamanho porque o PyPI reordenou a lista — a US-07
    leria um crescimento que não houve.
    """
    wheels = [
        {"packagetype": "bdist_wheel", "filename": "n-2.0.0-cp311-macosx.whl", "size": 21_219_203},
        {"packagetype": "bdist_wheel", "filename": "n-2.0.0-cp311-manylinux.whl", "size": 4_977_729},
        {"packagetype": "bdist_wheel", "filename": "n-2.0.0-cp312-win.whl", "size": 6_000_000},
    ]
    data = {"info": {"version": "2.0.0"}, "releases": {"2.0.0": wheels}}
    reordered = {"info": {"version": "2.0.0"}, "releases": {"2.0.0": list(reversed(wheels))}}

    assert get_release_size(data, "2.0.0") == get_release_size(reordered, "2.0.0")


def test_versao_ausente_nao_tem_tamanho_nem_idade():
    """Versão que não consta em `releases` devolve None (indisponível, não zero)."""
    assert get_release_size(_SAMPLE, "9.9.9") is None
    assert get_release_age_days(_SAMPLE, "9.9.9", today=date(2024, 1, 20)) is None


def test_idade_e_dias_desde_o_upload_da_versao():
    """Idade é hoje menos o upload_time da própria versão (ADR-0004)."""
    age = get_release_age_days(_SAMPLE, "2.0.0", today=date(2024, 1, 20))

    assert age == 10
