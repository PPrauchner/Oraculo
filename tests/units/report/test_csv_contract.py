"""
Guarda o CSV como contrato: cabeçalho e valores fixos, alheios à língua da tela.

A US-07 depende de que quaisquer dois exports do mesmo Projeto-Alvo se concatenem
numa série temporal. Isso só vale se o arquivo não mudar de forma por motivo de
tela — nem pelo seletor de língua, nem por uma renomeação de chave interna feita
por razão de código.

O cabeçalho era efeito colateral do dicionário: `export_to_csv` o derivava de
`report_data[0].keys()`. A ADR-0008 decidiu que ele passasse a ser escolha
explícita, e é essa separação que estes testes guardam — não basta o cabeçalho
estar certo hoje, ele precisa ser *incapaz* de mudar sozinho quando a chave mudar.

Responsabilidades:
- Guardar o cabeçalho em inglês, na ordem do esquema.
- Guardar que o cabeçalho não segue as chaves internas.
- Guardar que os valores do arquivo também não falam português.
"""

import csv
import io

import pytest

import utils.i18n
from core.report.export import CSV_HEADER, export_to_csv
from core.report.normalization import build_export_rows
from utils.i18n import available_languages
from utils.constants import (
    CATEGORY_ZOMBIE,
    ORIGIN_DEVELOPMENT,
    ORIGIN_PRODUCTION,
    ORIGIN_UNAVAILABLE,
    OUTDATED_YES,
    STATUS_OUTDATED,
    STATUS_UP_TO_DATE,
    UNKNOWN,
)
from utils.types import ExportRow

# O cabeçalho que o usuário abre no Excel. Title case, em inglês, e estável:
# mexer nesta lista é mexer no contrato, e é para isso que ela está à vista.
EXPECTED_HEADER = [
    "Analysis Date",
    "Project",
    "Package",
    "Category",
    "Origin",
    "Used Version",
    "PyPI Version",
    "Outdated",
    "Size",
    "Age",
]


def _export(analysis_date: str = "2026-07-20") -> bytes:
    """Exporta um conjunto auditado mínimo: um Zumbi Desatualizado e uma saudável."""
    dependencies = [
        {
            "package": "altair",
            "origin": ORIGIN_PRODUCTION,
            "used_version": "4.0.0",
            "pypi_version": "5.2.0",
            "status": STATUS_OUTDATED,
            "size": 524288,
            "age": 400,
        },
        {
            "package": "pytest",
            "origin": ORIGIN_DEVELOPMENT,
            "used_version": "8.0.0",
            "pypi_version": "8.0.0",
            "status": STATUS_UP_TO_DATE,
            "size": 8388608,
            "age": 10,
        },
    ]
    rows = build_export_rows(
        dependencies,
        zombies=[dependencies[0]],
        ghosts=[],
        project_name="grupo-03",
        analysis_date=analysis_date,
    )
    return export_to_csv(rows)


def _rows() -> list[dict]:
    """Lê o CSV exportado de volta, como um consumidor a jusante leria."""
    return list(csv.DictReader(io.StringIO(_export().decode("utf-8"))))


def test_o_cabecalho_sai_em_ingles_na_ordem_do_esquema():
    """O arquivo baixado abre com as colunas do esquema, em inglês."""
    header = _export().decode("utf-8").splitlines()[0]

    assert header.split(",") == EXPECTED_HEADER


def test_o_cabecalho_nao_segue_as_chaves_internas():
    """A prova do desacoplamento: rótulo e chave são vocabulários distintos.

    Enquanto o cabeçalho saía de `.keys()`, renomear uma chave por razão de
    código reescrevia o arquivo exportado em silêncio. Se estes dois conjuntos
    coincidissem, o acoplamento estaria de volta na prática, ainda que o código
    aparentasse mapear.
    """
    assert EXPECTED_HEADER != list(ExportRow.__annotations__)


def test_todo_campo_da_exportacao_tem_rotulo_de_cabecalho():
    """Campo sem rótulo sairia do arquivo calado, levando um dado junto."""
    assert list(CSV_HEADER) == list(ExportRow.__annotations__)
    assert list(CSV_HEADER.values()) == EXPECTED_HEADER


def test_a_categoria_exportada_nao_fala_portugues():
    """Categoria é dado do arquivo, não rótulo de tela: fixa e em inglês."""
    zombie = next(row for row in _rows() if row["Package"] == "altair")

    assert zombie["Category"] == CATEGORY_ZOMBIE
    assert CATEGORY_ZOMBIE == "Zombie"


def test_a_origem_exportada_nao_fala_portugues():
    """Origem distingue Produção de Desenvolvimento e vai crua para o arquivo."""
    origins = {row["Package"]: row["Origin"] for row in _rows()}

    assert origins == {"altair": "Production", "pytest": "Development"}


def test_a_marca_de_desatualizada_nao_fala_portugues():
    """A coluna Desatualizada é booleano legível — e legível em inglês."""
    zombie = next(row for row in _rows() if row["Package"] == "altair")

    assert zombie["Outdated"] == OUTDATED_YES
    assert OUTDATED_YES == "Yes"


def test_o_arquivo_sai_byte_identico_em_qualquer_lingua_da_tela():
    """A garantia central da ADR-0008, e a razão de a US-07 existir.

    Auditar o mesmo Projeto-Alvo com a tela em português em março e em inglês em
    junho tem de produzir arquivos que se concatenam. Se o seletor alcançasse o
    export, a série temporal quebraria em silêncio — sem erro e sem aviso, que é o
    pior modo de falhar para um dado histórico.

    O teste roda o mesmo export sob cada língua disponível: uma língua nova entra
    na comparação sozinha, sem ninguém editar este arquivo.
    """
    monkeypatch = pytest.MonkeyPatch()
    exported = {}

    try:
        for language in available_languages():
            monkeypatch.setattr(utils.i18n.st, "query_params", {"lang": language})
            exported[language] = _export()
    finally:
        monkeypatch.undo()

    assert len(exported) > 1, "só há uma língua — a comparação não prova nada"
    assert len(set(exported.values())) == 1


def test_o_indeterminado_e_o_nao_aplicavel_nao_se_confundem_no_arquivo():
    """Duas ausências distintas escrevem dois tokens distintos (CONTEXT.md).

    `N/A` diz "não existe por definição": é a Origem de um Fantasma, que não vem de
    Declaração nenhuma — nenhum arquivo a mais a preencheria. `Unknown` diz "o
    ORÁCULO não tem como saber": é o Tamanho e a Idade sem Versão Usada resolvida,
    e um Lock resolveria.

    Colapsar os dois num token só apagaria, para quem lê o arquivo, a diferença
    entre um dado que falta e um dado que não cabe — e é a primeira que diz ao
    usuário que adotar um Lock melhoraria o relatório dele.
    """
    ghost = {"package": "requests", "used_version": "N/A"}  # sem Origem
    unresolved = {"package": "ruff", "origin": ORIGIN_DEVELOPMENT}  # sem Versão Usada

    rows = build_export_rows(
        [ghost, unresolved],
        zombies=[],
        ghosts=[ghost],
        project_name="grupo-03",
        analysis_date="2026-07-20",
    )
    by_package = {row["package"]: row for row in rows}

    assert by_package["requests"]["origin"] == ORIGIN_UNAVAILABLE == "N/A"
    assert by_package["ruff"]["size"] == UNKNOWN == "Unknown"
    assert by_package["ruff"]["age"] == UNKNOWN
