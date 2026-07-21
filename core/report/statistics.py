"""
Size and Age statistics stratified by Category (US-06).

Responsibilities:
- Aggregate Count, summed Size and average Age of the dependencies of a category.
- Count the dependencies left out for having unavailable Size/Age.
- Describe these aggregations for display, making explicit how many were left out.

Describe, not word: the caption leaves here as identity and data, and the text
is born in `utils/display.py`, in the screen language (ADR-0010).
"""

from utils.types import CategorySummary, SummaryMetric


def _available(dependencies: list[dict], metric: str) -> list[float]:
    """Numeric values of a metric, discarding the unavailable ones.

    Without a resolved Used Version, Size and Age come out as the unavailability
    sentinel (ADR-0002/ADR-0004). Summing or averaging that sentinel as 0
    would invent a number that PyPI did not give.

    Args:
        dependencies: Dependencies of the category.
        metric: "size" or "age".

    Returns:
        Only the values actually measured.
    """
    values = [dep.get(metric) for dep in dependencies]
    return [value for value in values if isinstance(value, (int, float))]


def summarize_category(dependencies: list[dict]) -> CategorySummary:
    """Aggregates Count, Size and Age of the dependencies of a category.

    Args:
        dependencies: Dependencies of the category.

    Returns:
        `count` (all the dependencies of the category), `total_size` and `average_age`
        (only those actually measured, or ``None`` when none were), and
        `missing_size`/`missing_age` with how many were left out of each aggregation.
    """
    sizes = _available(dependencies, "size")
    ages = _available(dependencies, "age")

    return {
        "count": len(dependencies),
        "total_size": sum(sizes) if sizes else None,
        "average_age": sum(ages) / len(ages) if ages else None,
        "missing_size": len(dependencies) - len(sizes),
        "missing_age": len(dependencies) - len(ages),
    }


def summarize_by_category(report: dict[str, list[dict]]) -> dict[str, CategorySummary]:
    """Stratifies the statistics by Category (US-06).

    Walks the categories the report brings, with no fixed list: adding
    a new category to the report is enough for it to appear in the statistics.

    Args:
        report: Category (label) to the dependencies that compose it.

    Returns:
        One `summarize_category` aggregation per category, in the same order.
    """
    return {
        category_label: summarize_category(dependencies)
        for category_label, dependencies in report.items()
    }


def summary_metrics(summary: CategorySummary) -> list[SummaryMetric]:
    """Describes the statistics of a category for whoever will display them.

    Returns the metric's identity and the data that describe it, not the sentence
    (ADR-0010). The previous one — "Tamanho: 1.2 MB (1 de 2 sem dado)" — was born ready and
    in Portuguese in here, and under `?lang=en` reached the screen with nothing to translate.

    The count of how many were left out travels alongside the value on purpose: an
    average Age computed over half the packages, without warning, misleads the reader.

    Args:
        summary: Aggregation produced by `summarize_category`.

    Returns:
        The summed Size and the average Age, in this order, each with how many
        dependencies were left out of the aggregation and out of how many.
    """
    total = summary["count"]

    return [
        {
            "metric": "size",
            "value": summary["total_size"],
            "missing": summary["missing_size"],
            "total": total,
        },
        {
            "metric": "age",
            "value": summary["average_age"],
            "missing": summary["missing_age"],
            "total": total,
        },
    ]
