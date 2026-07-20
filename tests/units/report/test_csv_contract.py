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

from core.report.export import CSV_HEADER, export_to_csv
from core.report.normalization import build_export_rows
from utils.constants import (
    CATEGORY_ZOMBIE,
    ORIGIN_DEVELOPMENT,
    ORIGIN_PRODUCTION,
    OUTDATED_YES,
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
            "Origem": ORIGIN_PRODUCTION,
            "Versão Usada": "4.0.0",
            "Versão PyPI": "5.2.0",
            "Status": "Desatualizado",
            "Tamanho": 524288,
            "Idade": 400,
        },
        {
            "package": "pytest",
            "Origem": ORIGIN_DEVELOPMENT,
            "Versão Usada": "8.0.0",
            "Versão PyPI": "8.0.0",
            "Status": "Atualizado",
            "Tamanho": 8388608,
            "Idade": 10,
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
