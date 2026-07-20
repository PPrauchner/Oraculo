"""
Testes do analisador de dependências desatualizadas.

Garantem a régua da Versão Usada (ADR-0002):
- sem Versão Usada, não se afirma que o pacote está Atualizado nem se inventa a
  versão do PyPI;
- com um pin, compara-se a Versão Usada contra a última versão publicada.

E o Tamanho/Idade a partir dos metadados do PyPI (ADR-0004):
- vêm da Versão Usada, não da versão mais recente;
- Fantasma (sem Declaração) usa a versão mais recente como referência;
- Versão Usada N/D de uma Dependência Declarada fica indisponível, nunca 0;
- pacote ausente do PyPI não quebra a análise dos demais.
"""

from unittest.mock import patch

from core.analysis.outdated_analizer import analyze_dependency_status
from utils.constants import (
    STATUS_OUTDATED,
    STATUS_UNKNOWN,
    STATUS_UP_TO_DATE,
    VERSION_UNAVAILABLE,
)


def _release(packagetype, size, upload_time="2020-01-01T00:00:00"):
    return {"packagetype": packagetype, "size": size, "upload_time": upload_time}


def _data(latest, releases):
    """Monta uma resposta do PyPI com versão mais recente e releases."""
    return {"info": {"version": latest}, "releases": releases}


def _with_pypi_data(data):
    """Fixa os metadados que o PyPI devolveria para qualquer pacote."""
    return patch(
        "core.analysis.outdated_analizer.fetch_package_data",
        return_value=data,
    )


_DEFAULT = _data(
    "3.0.1",
    {
        "1.5.0": [_release("bdist_wheel", 100)],
        "3.0.1": [_release("bdist_wheel", 999)],
    },
)


def test_versao_usada_n_d_nao_e_reportada_como_atualizado():
    """Sem Versão Usada, não dá para afirmar que está atualizado (ADR-0002)."""
    deps = [{"package": "pandas", "used_version": "", "origin": "Production"}]

    with _with_pypi_data(_DEFAULT):
        result = analyze_dependency_status(deps)

    assert result[0]["status"] != STATUS_UP_TO_DATE
    assert result[0]["used_version"] == VERSION_UNAVAILABLE


def test_versao_usada_n_d_nao_copia_versao_do_pypi():
    """Sem Versão Usada, a versão do PyPI não vira Versão Usada (ADR-0002)."""
    deps = [{"package": "pandas", "used_version": "", "origin": "Production"}]

    with _with_pypi_data(_DEFAULT):
        result = analyze_dependency_status(deps)

    assert result[0]["used_version"] != "3.0.1"


def test_pin_anterior_a_ultima_e_desatualizado():
    """Uma Versão Usada anterior à última publicada é Desatualizada."""
    deps = [{"package": "pandas", "used_version": "1.5.0", "origin": "Production"}]

    with _with_pypi_data(_DEFAULT):
        result = analyze_dependency_status(deps)

    assert result[0]["status"] == STATUS_OUTDATED


def test_pin_na_ultima_versao_e_atualizado():
    """Uma Versão Usada igual à última publicada é Atualizada."""
    deps = [{"package": "pandas", "used_version": "3.0.1", "origin": "Production"}]

    with _with_pypi_data(_DEFAULT):
        result = analyze_dependency_status(deps)

    assert result[0]["status"] == STATUS_UP_TO_DATE


def test_tamanho_e_idade_sao_da_versao_usada_nao_da_mais_recente():
    """Tamanho/Idade referem a Versão Usada, não a versão mais recente (ADR-0004)."""
    deps = [{"package": "pandas", "used_version": "1.5.0", "origin": "Production"}]

    with _with_pypi_data(_DEFAULT):
        result = analyze_dependency_status(deps)

    assert result[0]["size"] == 100  # wheel da 1.5.0, não os 999 da 3.0.1
    assert isinstance(result[0]["age"], int)


def test_versao_usada_n_d_declarada_tem_tamanho_e_idade_indisponiveis():
    """Dependência Declarada sem Versão Usada: Tamanho/Idade indisponíveis, nunca 0."""
    deps = [{"package": "pandas", "used_version": "", "origin": "Production"}]

    with _with_pypi_data(_DEFAULT):
        result = analyze_dependency_status(deps)

    assert result[0]["size"] == VERSION_UNAVAILABLE
    assert result[0]["age"] == VERSION_UNAVAILABLE


def test_fantasma_usa_tamanho_e_idade_da_versao_mais_recente():
    """Fantasma não tem Declaração/Versão Usada: usa a versão mais recente."""
    ghost = [{"package": "requests", "used_version": "N/A"}]  # sem Origem

    with _with_pypi_data(_DEFAULT):
        result = analyze_dependency_status(ghost)

    assert result[0]["size"] == 999  # wheel da 3.0.1 (mais recente)
    assert isinstance(result[0]["age"], int)


def test_pacote_ausente_do_pypi_nao_quebra_os_demais():
    """Pacote inexistente no PyPI fica indisponível sem afetar os outros."""
    deps = [
        {"package": "pacote-interno", "used_version": "1.0.0", "origin": "Production"},
        {"package": "pandas", "used_version": "1.5.0", "origin": "Production"},
    ]

    def fake_fetch(name):
        return None if name == "pacote-interno" else _DEFAULT

    with patch(
        "core.analysis.outdated_analizer.fetch_package_data", side_effect=fake_fetch
    ):
        result = analyze_dependency_status(deps)

    by_name = {dep["package"]: dep for dep in result}
    assert by_name["pacote-interno"]["size"] == VERSION_UNAVAILABLE
    assert by_name["pacote-interno"]["age"] == VERSION_UNAVAILABLE
    assert by_name["pacote-interno"]["status"] == STATUS_UNKNOWN
    assert by_name["pandas"]["size"] == 100  # os demais seguem analisados


def test_versao_com_sufixo_pep_440_le_a_propria_release():
    """`2.0.0b1` não é `2.0.0`: Tamanho/Idade saem da release da Versão Usada."""
    data = _data(
        "2.0.0",
        {
            "2.0.0b1": [_release("bdist_wheel", 111)],
            "2.0.0": [_release("bdist_wheel", 999)],
        },
    )
    deps = [{"package": "pandas", "used_version": "2.0.0b1", "origin": "Production"}]

    with _with_pypi_data(data):
        result = analyze_dependency_status(deps)

    assert result[0]["size"] == 111  # a pré-release, não os 999 da final
    assert result[0]["status"] == STATUS_OUTDATED  # 2.0.0b1 < 2.0.0


def test_versao_post_release_le_a_propria_release():
    """`2.9.0.post0` (forma que o uv.lock deste projeto pina) não vira `2.9.0`."""
    data = _data(
        "2.9.0.post0",
        {
            "2.9.0": [_release("bdist_wheel", 100)],
            "2.9.0.post0": [_release("bdist_wheel", 222)],
        },
    )
    deps = [{"package": "pandas", "used_version": "2.9.0.post0", "origin": "Production"}]

    with _with_pypi_data(data):
        result = analyze_dependency_status(deps)

    assert result[0]["size"] == 222
    assert result[0]["status"] == STATUS_UP_TO_DATE


def test_versao_usada_que_nao_e_pep_440_conta_como_indisponivel():
    """Um valor que não é versão PEP 440 não vira chave de `releases[]`."""
    deps = [{"package": "pandas", "used_version": "não-é-versão", "origin": "Production"}]

    with _with_pypi_data(_DEFAULT):
        result = analyze_dependency_status(deps)

    assert result[0]["used_version"] == VERSION_UNAVAILABLE
    assert result[0]["size"] == VERSION_UNAVAILABLE


def test_fantasma_ausente_do_pypi_reporta_versao_usada_indisponivel():
    """Fantasma cujo Nome de Import não existe no PyPI (`yaml`) reporta N/D.

    O sentinela é o mesmo do caminho com PyPI: não conhecer a Versão Usada é
    indisponibilidade, não um "N/A" herdado do extrator de imports.
    """
    ghost = [{"package": "yaml", "used_version": "N/A"}]  # sem Origem

    with patch(
        "core.analysis.outdated_analizer.fetch_package_data", return_value=None
    ):
        result = analyze_dependency_status(ghost)

    assert result[0]["used_version"] == VERSION_UNAVAILABLE


def test_pin_de_pacote_ausente_do_pypi_e_preservado():
    """Pacote privado com pin mantém a Versão Usada que a Declaração fixou."""
    deps = [{"package": "pacote-interno", "used_version": "1.0.0", "origin": "Production"}]

    with patch(
        "core.analysis.outdated_analizer.fetch_package_data", return_value=None
    ):
        result = analyze_dependency_status(deps)

    assert result[0]["used_version"] == "1.0.0"


def test_resposta_do_pypi_sem_versao_nao_quebra_a_analise():
    """Resposta malformada é tratada como indisponível, não sobe KeyError."""
    deps = [
        {"package": "quebrado", "used_version": "1.0.0", "origin": "Production"},
        {"package": "pandas", "used_version": "1.5.0", "origin": "Production"},
    ]

    def fake_fetch(name):
        return {} if name == "quebrado" else _DEFAULT

    with patch(
        "core.analysis.outdated_analizer.fetch_package_data", side_effect=fake_fetch
    ):
        result = analyze_dependency_status(deps)

    by_name = {dep["package"]: dep for dep in result}
    assert by_name["quebrado"]["status"] == STATUS_UNKNOWN
    assert by_name["pandas"]["size"] == 100  # os demais seguem analisados


def test_um_unico_request_por_pacote():
    """Versão, Tamanho e Idade saem de um único request por pacote (AC3)."""
    deps = [{"package": "pandas", "used_version": "1.5.0", "origin": "Production"}]

    with patch(
        "core.analysis.outdated_analizer.fetch_package_data", return_value=_DEFAULT
    ) as mock_fetch:
        analyze_dependency_status(deps)

    assert mock_fetch.call_count == 1
