"""
Módulo responsável pela exportação de relatórios em formato CSV.

Converte estruturas de dados (ex: DataFrame) em arquivos CSV
para download ou armazenamento.

Entrada:
- Estrutura de dados tabular (dicionário)

Saída:
- Dados em formato CSV (bytes ou string)
"""

import csv
import io
import json

from utils.types import ExportRow

# Chave interna → rótulo da coluna no arquivo baixado.
#
# O cabeçalho era efeito colateral do dicionário: `export_to_csv` o derivava de
# `report_data[0].keys()`, então renomear uma chave por razão de código reescrevia
# o arquivo exportado sem que ninguém percebesse. A ADR-0008 tornou o cabeçalho
# escolha explícita, e é isto: os dois vocabulários ficam separados de propósito,
# para que mexer num não alcance o outro por acidente.
#
# A ordem é a ordem das colunas, e ela é contrato — a US-07 depende de que dois
# exports do mesmo Projeto-Alvo se concatenem numa série temporal.
CSV_HEADER = {
    "Data da Análise": "Analysis Date",
    "Projeto": "Project",
    "package": "Package",
    "Categoria": "Category",
    "origin": "Origin",
    "used_version": "Used Version",
    "pypi_version": "PyPI Version",
    "Desatualizada": "Outdated",
    "size": "Size",
    "Idade": "Age",
}


def _as_csv_row(row: ExportRow) -> dict[str, object]:
    """Traduz uma linha interna para os rótulos do cabeçalho.

    A travessia passa por um `dict` comum de propósito: num `TypedDict` a chave
    precisa ser literal, e aqui ela vem do mapeamento. É também onde os dois
    vocabulários se encontram — o único ponto do código em que isso acontece.

    Args:
        row: Linha da exportação, com as chaves internas.

    Returns:
        A mesma linha, com os rótulos que o usuário lê no arquivo.
    """
    values: dict[str, object] = dict(row)

    return {label: values[key] for key, label in CSV_HEADER.items()}


def export_to_csv(report_data: list[ExportRow]) -> bytes:
    """
    Converte uma lista de dicionários em um arquivo CSV.

    Args:
        report_data: Linhas da exportação, na ordem das colunas do esquema.

    Returns:
        bytes: Conteúdo do arquivo CSV em formato de bytes.
    """

    if not report_data:
        return b""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(CSV_HEADER.values()))
    writer.writeheader()
    writer.writerows(_as_csv_row(row) for row in report_data)

    return output.getvalue().encode("utf-8")


def export_to_json(report_data: list[ExportRow]) -> bytes:
    """
    Converte uma lista de dicionários em um arquivo JSON.

    Args:
        report_data: Linhas da exportação, na ordem das colunas do esquema.

    Returns:
        bytes: Conteúdo do arquivo JSON em formato de bytes.
    """

    return json.dumps(report_data, indent=4).encode("utf-8")
