"""
Testes do analisador de dependências desatualizadas.

Garantem a régua da Versão Usada (ADR-0002):
- sem Versão Usada, não se afirma que o pacote está Atualizado nem se inventa a
  versão do PyPI;
- com um pin, compara-se a Versão Usada contra a última versão publicada.
"""

from unittest.mock import patch

from core.analysis.outdated_analizer import analyze_dependency_status
from utils.constants import VERSION_UNAVAILABLE


def _with_pypi_version(version):
    """Fixa a versão que o PyPI devolveria para qualquer pacote."""
    return patch(
        "core.analysis.outdated_analizer.get_latest_version",
        return_value=version,
    )


def test_versao_usada_n_d_nao_e_reportada_como_atualizado():
    """Sem Versão Usada, não dá para afirmar que está atualizado (ADR-0002)."""
    deps = [{"Pacote": "pandas", "Versão Usada": ""}]

    with _with_pypi_version("3.0.1"):
        result = analyze_dependency_status(deps)

    assert result[0]["Status"] != "Atualizado"
    assert result[0]["Versão Usada"] == VERSION_UNAVAILABLE


def test_versao_usada_n_d_nao_copia_versao_do_pypi():
    """Sem Versão Usada, a versão do PyPI não vira Versão Usada (ADR-0002)."""
    deps = [{"Pacote": "pandas", "Versão Usada": ""}]

    with _with_pypi_version("3.0.1"):
        result = analyze_dependency_status(deps)

    assert result[0]["Versão Usada"] != "3.0.1"


def test_pin_anterior_a_ultima_e_desatualizado():
    """Uma Versão Usada anterior à última publicada é Desatualizada."""
    deps = [{"Pacote": "pandas", "Versão Usada": "1.5.0"}]

    with _with_pypi_version("3.0.1"):
        result = analyze_dependency_status(deps)

    assert result[0]["Status"] == "Desatualizado"


def test_pin_na_ultima_versao_e_atualizado():
    """Uma Versão Usada igual à última publicada é Atualizada."""
    deps = [{"Pacote": "pandas", "Versão Usada": "3.0.1"}]

    with _with_pypi_version("3.0.1"):
        result = analyze_dependency_status(deps)

    assert result[0]["Status"] == "Atualizado"
