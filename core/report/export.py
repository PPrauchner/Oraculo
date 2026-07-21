"""
CSV report exporting.

Converts data structures (e.g.: DataFrame) into CSV files
for download or storage.

Input:
- Tabular data structure (dictionary)

Output:
- Data in CSV format (bytes or string)
"""

import csv
import io
import json

from utils.types import ExportRow

# Internal key → column label in the downloaded file.
#
# The header used to be a side effect of the dictionary: `export_to_csv` derived it from
# `report_data[0].keys()`, so renaming a key for a code reason rewrote
# the exported file without anyone noticing. ADR-0008 made the header an
# explicit choice, and this is it: the two vocabularies stay separated on purpose,
# so that touching one does not reach the other by accident.
#
# The order is the order of the columns, and it is a contract — US-07 depends on two
# exports of the same Target Project concatenating into a time series.
CSV_HEADER = {
    "analysis_date": "Analysis Date",
    "project": "Project",
    "package": "Package",
    "category": "Category",
    "origin": "Origin",
    "used_version": "Used Version",
    "pypi_version": "PyPI Version",
    "outdated": "Outdated",
    "size": "Size",
    "age": "Age",
}


def _as_csv_row(row: ExportRow) -> dict[str, object]:
    """Translates an internal row to the header labels.

    The traversal goes through a plain `dict` on purpose: in a `TypedDict` the key
    must be a literal, and here it comes from the mapping. It is also where the two
    vocabularies meet — the only point in the code where that happens.

    Args:
        row: Export row, with the internal keys.

    Returns:
        The same row, with the labels the user reads in the file.
    """
    values: dict[str, object] = dict(row)

    return {label: values[key] for key, label in CSV_HEADER.items()}


def export_to_csv(report_data: list[ExportRow]) -> bytes:
    """
    Converts a list of dictionaries into a CSV file.

    Args:
        report_data: Export rows, in the order of the schema columns.

    Returns:
        bytes: CSV file content as bytes.
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
    Converts a list of dictionaries into a JSON file.

    Args:
        report_data: Export rows, in the order of the schema columns.

    Returns:
        bytes: JSON file content as bytes.
    """

    return json.dumps(report_data, indent=4).encode("utf-8")
