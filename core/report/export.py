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
    writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
    writer.writeheader()
    writer.writerows(report_data)

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
