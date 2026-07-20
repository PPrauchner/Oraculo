"""
Testes da exportação do relatório.

Garante que o CSV entregue ao usuário carrega o esquema da US-06/US-07 — com
Data da Análise, Categoria e Origem — e que exportações de datas diferentes se
concatenam em uma série temporal analisável.
"""

import csv
import io

from core.report.export import export_to_csv
from core.report.normalization import build_export_rows
from utils.constants import CATEGORY_ZOMBIE, ORIGIN_PRODUCTION, OUTDATED_YES

# Os rótulos do cabeçalho, e não as chaves internas: desde a ADR-0008 os dois
# vocabulários são separados, e é pelo primeiro que um consumidor lê o arquivo.
EXPORT_SCHEMA = [
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


def _dependencies() -> list[dict]:
    """Conjunto auditado mínimo: um Zumbi Desatualizado e uma dependência saudável."""
    return [
        {
            "package": "altair",
            "origin": ORIGIN_PRODUCTION,
            "used_version": "4.0.0",
            "pypi_version": "5.2.0",
            "status": "Desatualizado",
            "size": 524288,
            "Idade": 400,
        },
        {
            "package": "streamlit",
            "origin": ORIGIN_PRODUCTION,
            "used_version": "1.40.0",
            "pypi_version": "1.40.0",
            "status": "Atualizado",
            "size": 8388608,
            "Idade": 10,
        },
    ]


def _export(analysis_date: str) -> bytes:
    """Exporta o conjunto auditado como CSV na data indicada."""
    dependencies = _dependencies()
    rows = build_export_rows(
        dependencies,
        zombies=[dependencies[0]],
        ghosts=[],
        project_name="grupo-03",
        analysis_date=analysis_date,
    )
    return export_to_csv(rows)


def _read(csv_bytes: bytes) -> list[dict]:
    """Lê o CSV exportado de volta como lista de dicionários."""
    return list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))


def test_csv_header_follows_the_export_schema():
    """O cabeçalho traz as colunas do esquema, na ordem definida."""
    content = _export("2026-07-18").decode("utf-8")
    header = content.splitlines()[0]

    assert header.split(",") == EXPORT_SCHEMA


def test_csv_has_one_row_per_dependency_without_duplicates():
    """Uma linha por dependência auditada — inclusive a que é Zumbi e Desatualizada."""
    rows = _read(_export("2026-07-18"))
    packages = [row["Package"] for row in rows]

    assert packages == ["altair", "streamlit"]
    assert len(packages) == len(set(packages))


def test_csv_marks_zombie_and_outdated_on_the_same_row():
    """Categoria Zumbi e Desatualizada convivem na mesma linha do CSV."""
    rows = _read(_export("2026-07-18"))
    zombie_row = next(row for row in rows if row["Package"] == "altair")

    assert zombie_row["Category"] == CATEGORY_ZOMBIE
    assert zombie_row["Outdated"] == OUTDATED_YES
    assert zombie_row["Origin"] == ORIGIN_PRODUCTION


def test_concatenating_two_exports_yields_a_time_series():
    """Concatenar CSVs de datas diferentes dá a série temporal da US-07."""
    first = _export("2026-07-11")
    second = _export("2026-07-18")

    # Concatenação real: o cabeçalho do segundo arquivo é descartado.
    concatenated = first + b"\n".join(second.splitlines()[1:]) + b"\n"
    rows = _read(concatenated)

    dates = sorted({row["Analysis Date"] for row in rows})
    altair_history = [row for row in rows if row["Package"] == "altair"]

    assert dates == ["2026-07-11", "2026-07-18"]
    assert len(rows) == 4
    assert [row["Analysis Date"] for row in altair_history] == dates
