"""
Translates the data `core/report/` returns into the text the report shows.

Responsibilities:
- Format raw Size and Age in the unit and the language of the screen.
- Label Status and Origin from the stable identity that `core/` returns.
- Assemble the table rows already with the columns labeled.

It is the same role that `utils/messages.py` plays for the error codes of
`core/ingestion/`: `core/` returns identity and data, and the wording, the unit and the
language are a decision of whoever renders (ADR-0010). Before this `normalize` returned
"30 dias" and "(última versão)" ready-made — with `?lang=en` the table answered in
Portuguese, and there was nothing left to translate because the data had already become a phrase.

It lives in `utils/` and not inside `pages/report.py` for two reasons: the page
runs Streamlit on import, and nothing that only it can import is testable
as a module; and the same data goes out in the table and in the metrics.

This is the project's third vocabulary, alongside the internal keys (snake_case)
and the CSV header (`CSV_HEADER`, Title Case fixed in English). They are separated on
purpose: translating the screen cannot reach the exported file (ADR-0008).
"""

from typing import Callable

from utils.constants import (
    ORIGIN_DEVELOPMENT,
    ORIGIN_PRODUCTION,
    ORIGIN_UNAVAILABLE,
    STATUS_INVALID_VERSION,
    STATUS_OUTDATED,
    STATUS_UP_TO_DATE,
    UNKNOWN,
)
from utils.i18n import t
from utils.types import RawMetric, ReportRow, SummaryMetric

_BYTES_PER_KB = 1024
_BYTES_PER_MB = 1024 * 1024

# Internal row key → column locale key. The order is the order in which the
# columns appear in the table; the internal key never reaches the screen, because it is
# the CSV contract and changing it for a screen reason would rewrite the file (ADR-0008).
REPORT_COLUMNS = {
    "package": "report.column.package",
    "used_version": "report.column.used_version",
    "pypi_version": "report.column.pypi_version",
    "status": "report.column.status",
    "size": "report.column.size",
    "age": "report.column.age",
    "origin": "report.column.origin",
}

# The Indeterminate does not appear here: it is the absence, and `_value_label` already resolves it.
# Registering it again would create two locale keys for the same text.
STATUS_KEYS = {
    STATUS_OUTDATED: "report.status.outdated",
    STATUS_UP_TO_DATE: "report.status.up_to_date",
    STATUS_INVALID_VERSION: "report.status.invalid_version",
}

ORIGIN_KEYS = {
    ORIGIN_PRODUCTION: "report.origin.production",
    ORIGIN_DEVELOPMENT: "report.origin.development",
}


def _value_label(value: str) -> str:
    """Label of the two absences; any other value is package data.

    `CONTEXT.md` separates Indeterminate ("the ORÁCULO has no way to know") from Not
    Applicable ("does not exist by definition"), and the screen needs to keep the distinction:
    only the first tells the user that adopting a Lock would improve their report.

    Args:
        value: Row value, already as stable identity.

    Returns:
        The translated label when the value is one of the absences; the value itself
        when it is package data — name and number are not translated.
    """
    if value == UNKNOWN:
        return t("report.value.unknown")
    if value == ORIGIN_UNAVAILABLE:
        return t("report.value.not_applicable")
    return value


def format_size(size: RawMetric) -> str:
    """Formats the raw Size (bytes) into the readable unit.

    Args:
        size: Bytes of the Used Version, or the Indeterminate when not measured.

    Returns:
        "X.Y MB" from 1 MB up, "X.Y KB" below that — never 0 for the not-measured
        case. KB and MB are unit symbols, not words: they do not change with the language.
    """
    if not isinstance(size, (int, float)):
        return _value_label(size)

    if size >= _BYTES_PER_MB:
        return f"{size / _BYTES_PER_MB:.1f} MB"
    return f"{size / _BYTES_PER_KB:.1f} KB"


def format_age(age: RawMetric) -> str:
    """Formats the raw Age (whole days) into the text of the screen language.

    Args:
        age: Days since the publication of the Used Version, or the Indeterminate.

    Returns:
        The day count worded by the locale — the plural is a language decision and
        for that reason lives there, not here.
    """
    if not isinstance(age, (int, float)):
        return _value_label(age)

    days = int(age)
    key = "report.age.day" if days == 1 else "report.age.days"
    return t(key).format(days=days)


def status_label(status: str) -> str:
    """Label of a Status in the screen language.

    Args:
        status: Stable identity, as `core/analysis/` returns it.

    Returns:
        The text to display. The identity stays in English because it is compared to
        build the Outdated column of the CSV; what changes with the language is only the text.
    """
    key = STATUS_KEYS.get(status)
    return t(key) if key else _value_label(status)


def origin_label(origin: str) -> str:
    """Label of an Origin in the screen language.

    Args:
        origin: Stable identity (Production, Development) or the Not Applicable
            of a Ghost, which does not come from any Declaration.

    Returns:
        The text to display.
    """
    key = ORIGIN_KEYS.get(origin)
    return t(key) if key else _value_label(origin)


def _metric_text(
    raw: RawMetric, from_latest: bool, formatter: Callable[[RawMetric], str]
) -> str:
    """Formats Size/Age and makes explicit when the reference is the most recent version.

    Args:
        raw: Raw value of the metric.
        from_latest: Whether the metric refers to the most recent version on PyPI, and not to the
            Used Version — the case of the Ghost, which has no Declaration.
        formatter: `format_size` or `format_age`.

    Returns:
        The cell text, annotated when there is a number and it describes another version.
        Without a number there is nothing to annotate: the note says which version the number is of.
    """
    text = formatter(raw)
    if from_latest and isinstance(raw, (int, float)):
        return f"{text} ({t('report.metric.latest_version')})"
    return text


def _cells(row: ReportRow) -> dict[str, str]:
    """Translates each field of a row into its cell text."""
    from_latest = row["metrics_from_latest"]

    return {
        "package": row["package"],
        "used_version": _value_label(row["used_version"]),
        "pypi_version": _value_label(row["pypi_version"]),
        "status": status_label(row["status"]),
        "size": _metric_text(row["size"], from_latest, format_size),
        "age": _metric_text(row["age"], from_latest, format_age),
        "origin": origin_label(row["origin"]),
    }


def display_rows(rows: list[ReportRow]) -> list[dict[str, str]]:
    """Assembles the report table in the screen language.

    Args:
        rows: Rows as `normalize` returns them — raw data and stable identity.

    Returns:
        One row per dependency, keyed by the column label: it is the key that
        Streamlit uses as the table header. `metrics_from_latest` does not become a
        column — it annotates the Size and the Age, it is not data to display on its own.
    """
    table = []

    for row in rows:
        cells = _cells(row)
        table.append({t(key): cells[field] for field, key in REPORT_COLUMNS.items()})

    return table


# Metric identity → caption label and formatter of its value.
#
# The label repeats that of the table column ("Size", "Age") although it describes another
# thing: here it is the *summed* Size and the *average* Age of the category. Calling them
# "Total Size" and "Average Age", which is the precise wording, does not fit — `READING_MAX_WIDTH`
# fixes the body at 1100px and each metric gets ~148px, against the ~172px that the
# long label asks for, so the caption would break into two lines. The label's precision
# lost to the width, on purpose; what the metric aggregates is in `CategorySummary`
# and in `summary_metrics`, for whoever comes to work here.
SUMMARY_METRICS: dict[str, tuple[str, Callable[[RawMetric], str]]] = {
    "size": ("report.summary.total_size", format_size),
    "age": ("report.summary.average_age", format_age),
}


def format_summary_metric(metric: SummaryMetric) -> str:
    """Writes the caption of a category statistic, in the screen language.

    Args:
        metric: Identity and data as `summary_metrics` returns them.

    Returns:
        The line to display, annotated with how many dependencies were left out of the
        aggregation. The note disappears when there was no exclusion — there was nothing to exclude.
    """
    key, formatter = SUMMARY_METRICS[metric["metric"]]
    value = metric["value"]

    # The average Age comes out fractional and the screen counts whole days; the Size is already
    # an integer, so the same rounding serves both without branching.
    raw: RawMetric = UNKNOWN if value is None else round(value)
    line = f"{t(key)}: {formatter(raw)}"

    if metric["missing"]:
        note = t("report.summary.missing").format(
            missing=metric["missing"], total=metric["total"]
        )
        return f"{line} {note}"

    return line
