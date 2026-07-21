"""
Guarda o Status como identidade estável, não como texto de tela.

O valor de Status não é só exibido: `build_export_rows` e `pages/report.py`
comparam contra ele para decidir o que é Desatualizada. Traduzir o valor junto com
o rótulo quebraria as duas comparações em silêncio — sem erro, sem linha a menos no
arquivo, só a coluna Outdated saindo "No" para todo mundo e a aba Desatualizadas
vazia.

É o mesmo par que a #47 estabeleceu para a Categoria: identidade em inglês, estável,
e rótulo resolvido por `t()` na renderização (ADR-0009/ADR-0010). O vocabulário é o
que o `CONTEXT.md` tabula, e `Unknown` é o Indeterminado — a ausência que um Lock
resolveria —, distinto do `N/A` do Não Aplicável.

Responsabilidades:
- Guardar os quatro valores de Status que o `CONTEXT.md` tabula.
- Guardar que `core/` só emite valores desse vocabulário.
- Guardar que nenhum status em português sobrou dentro de `core/`.
"""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from core.analysis.outdated_analizer import analyze_dependency_status
from core.parsin.dependency_parser import parse_dependencies
from utils.constants import (
    STATUS_INVALID_VERSION,
    STATUS_OUTDATED,
    STATUS_UNKNOWN,
    STATUS_UP_TO_DATE,
)

CORE_DIR = Path(__file__).resolve().parents[2] / "core"

# O vocabulário do `CONTEXT.md`, escrito à mão de propósito: se alguém trocar o valor
# de uma constante, é aqui que a mudança de contrato aparece em vez de passar batida.
STATUS_VOCABULARY = {"Outdated", "Up to date", "Unknown", "Invalid version"}

# Os status que `core/` emitia em português. Um deles de volta significa que a camada
# de domínio voltou a decidir em que língua o relatório fala.
PORTUGUESE_STATUS = re.compile(
    r"\"(Desatualizado|Atualizado|Desconhecido|Versão Inválida)\""
)


def _release(size: int) -> dict:
    return {"packagetype": "bdist_wheel", "size": size, "upload_time": "2020-01-01T00:00:00"}


_PYPI_DATA = {
    "info": {"version": "3.0.1"},
    "releases": {"1.5.0": [_release(100)], "3.0.1": [_release(999)]},
}


def _analyze(used_version: str, data: dict | None = _PYPI_DATA) -> str:
    """Status de uma Dependência de Produção, com o PyPI fixado."""
    deps = [{"package": "pandas", "used_version": used_version, "origin": "Production"}]

    with patch(
        "core.analysis.outdated_analizer.fetch_package_data", return_value=data
    ):
        return analyze_dependency_status(deps)[0]["status"]


def test_as_constantes_de_status_sao_o_vocabulario_do_context():
    """Os quatro valores que o relatório e a exportação conhecem, em inglês."""
    assert {
        STATUS_OUTDATED,
        STATUS_UP_TO_DATE,
        STATUS_UNKNOWN,
        STATUS_INVALID_VERSION,
    } == STATUS_VOCABULARY


def test_pin_anterior_a_ultima_versao_recebe_a_identidade_de_desatualizado():
    """A identidade que `build_export_rows` compara para marcar a coluna Outdated."""
    assert _analyze("1.5.0") == STATUS_OUTDATED


def test_pin_na_ultima_versao_recebe_a_identidade_de_atualizado():
    assert _analyze("3.0.1") == STATUS_UP_TO_DATE


def test_pacote_ausente_do_pypi_e_indeterminado():
    """Sem resposta do PyPI não se sabe o status: Indeterminado, não "atualizado"."""
    assert _analyze("1.0.0", data=None) == STATUS_UNKNOWN


def test_dependencia_declarada_sem_versao_usada_e_indeterminada():
    """Sem Lock e sem pin, o Status é a mesma ausência do Tamanho e da Idade.

    Este caminho reportava o sentinela de Versão Usada ("N/D") como se fosse status.
    São a mesma ausência — Indeterminado (ADR-0002) —, e agora dizem isso com a
    mesma palavra.
    """
    assert _analyze("") == STATUS_UNKNOWN


def test_a_analise_so_emite_status_do_vocabulario():
    """Nenhum caminho de `_check_dependency` inventa um quinto valor."""
    emitted = {
        _analyze("1.5.0"),
        _analyze("3.0.1"),
        _analyze(""),
        _analyze("1.0.0", data=None),
        _analyze("1.0.0", data={}),
    }

    assert emitted <= STATUS_VOCABULARY


def test_a_dependencia_nasce_indeterminada_no_parser():
    """Antes de consultar o PyPI não há status a afirmar."""
    parsed = parse_dependencies([{"package": "pandas", "used_version": "1.5.0"}])

    assert parsed[0]["status"] == STATUS_UNKNOWN


@pytest.mark.parametrize(
    "module", sorted(CORE_DIR.rglob("*.py")), ids=lambda path: path.name
)
def test_core_nao_emite_status_em_portugues(module: Path):
    """A língua do Status é decisão de tela, como o ícone era (ADR-0010)."""
    found = PORTUGUESE_STATUS.findall(module.read_text(encoding="utf-8"))

    assert found == []
