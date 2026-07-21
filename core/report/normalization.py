"""
Building of the final report.

Organizes the data coming from the analysis into a structure suitable
for display and export (e.g.: DataFrame).

Input:
- List with all the dependencies
- Analysis results (Zombies, Ghosts, Outdated)

Output:
- Organized data structure (e.g.: Dictionary)
"""

from core.analysis.ghost_analizer import is_ghost
from utils.constants import (
    CATEGORY_GHOST,
    CATEGORY_HEALTHY,
    CATEGORY_ZOMBIE,
    ORIGIN_UNAVAILABLE,
    OUTDATED_NO,
    OUTDATED_YES,
    STATUS_OUTDATED,
    STATUS_UNKNOWN,
    UNKNOWN,
)
from utils.types import Dependency, ExportRow, ReportRow


def normalize(list_analyzed: list[Dependency]) -> list[ReportRow]:
    """Selects, from each Dependency, what the report table displays.

    Returns data and identity, never ready-made text: Size in bytes, Age in days,
    Status as stable identity. Whoever chooses unit, wording and language is
    `utils/display.py` (ADR-0010) — while this function returned "30 dias", the
    table answered in Portuguese under `?lang=en`.

    Args:
        list_analyzed: Dependencies with their analysis results.

    Returns:
        One row per dependency, or a Not Applicable row when there is
        none — the table needs a shape even when empty.
    """

    rows: list[ReportRow] = []

    for dep in list_analyzed:
        rows.append(
            {
                "package": dep.get("package", ORIGIN_UNAVAILABLE),
                "used_version": dep.get("used_version", ORIGIN_UNAVAILABLE),
                "pypi_version": dep.get("pypi_version", ORIGIN_UNAVAILABLE),
                "status": dep.get("status", STATUS_UNKNOWN),
                "size": dep.get("size", UNKNOWN),
                "age": dep.get("age", UNKNOWN),
                "origin": dep.get("origin", ORIGIN_UNAVAILABLE),
                # A Ghost has no Declaration, so it has no Used Version (CONTEXT.md):
                # its Size/Age refer to the most recent version on PyPI, and the
                # table needs to be able to say so.
                "metrics_from_latest": is_ghost(dep),
            }
        )

    if not rows:
        empty: ReportRow = {
            "package": ORIGIN_UNAVAILABLE,
            "used_version": ORIGIN_UNAVAILABLE,
            "pypi_version": ORIGIN_UNAVAILABLE,
            "status": ORIGIN_UNAVAILABLE,
            "size": ORIGIN_UNAVAILABLE,
            "age": ORIGIN_UNAVAILABLE,
            "origin": ORIGIN_UNAVAILABLE,
            "metrics_from_latest": False,
        }
        return [empty]
    return rows


def build_export_rows(
    dependencies: list[Dependency],
    zombies: list[Dependency],
    ghosts: list[Dependency],
    project_name: str,
    analysis_date: str,
) -> list[ExportRow]:
    """Builds the export rows (US-06/US-07), one per dependency.

    The schema adds a temporal axis (Analysis Date) and an identity axis
    (Project), and stratifies by Category (Zombie, Ghost, Healthy). Outdated
    is its own column — a dependency can be a Zombie *and* Outdated at the same
    time, which a single Category field would lose.

    Size and Age come out raw (bytes and whole days) or as the unavailability
    sentinel, never formatted nor 0: the CSV is for diffing/concatenation over
    time, not for direct human reading (that is `normalize`).

    Args:
        dependencies: All the audited dependencies (Declared + Ghosts),
            already deduplicated.
        zombies: Zombie dependencies identified by the analysis.
        ghosts: Ghost dependencies identified by the analysis.
        project_name: Target Project identifier (same value on every row).
        analysis_date: Analysis Date (same value on every export row).

    Returns:
        One row per dependency, in the order of the schema columns.
    """
    zombie_names = {dep["package"] for dep in zombies}
    ghost_names = {dep["package"] for dep in ghosts}

    rows: list[ExportRow] = []
    for dep in dependencies:
        package = dep.get("package", "N/A")

        if package in zombie_names:
            category = CATEGORY_ZOMBIE
        elif package in ghost_names:
            category = CATEGORY_GHOST
        else:
            category = CATEGORY_HEALTHY

        outdated = OUTDATED_YES if dep.get("status") == STATUS_OUTDATED else OUTDATED_NO

        rows.append(
            {
                "analysis_date": analysis_date,
                "project": project_name,
                "package": package,
                "category": category,
                # A Ghost has no Declaration, so it has no Origin (CONTEXT.md).
                "origin": dep.get("origin", ORIGIN_UNAVAILABLE),
                "used_version": dep.get("used_version", "N/A"),
                "pypi_version": dep.get("pypi_version", "N/A"),
                "outdated": outdated,
                "size": dep.get("size", UNKNOWN),
                "age": dep.get("age", UNKNOWN),
            }
        )

    return rows


def filter_export_rows(
    rows: list[ExportRow],
    categories: set[str],
    include_outdated: bool,
) -> list[ExportRow]:
    """Selects the requested export rows, without repeating any dependency.

    Outdated is not a Category, so it enters as a separate criterion. A row that
    satisfies both criteria (e.g.: Zombie *and* Outdated) comes out a single time —
    filtering preserves the one-row-per-dependency rule.

    Args:
        rows: Rows produced by `build_export_rows`.
        categories: Selected Categories (Zombie, Ghost, Healthy).
        include_outdated: Whether the Outdated Dependencies also enter.

    Returns:
        The selected rows, in the original order.
    """
    return [
        row
        for row in rows
        if row["category"] in categories
        or (include_outdated and row["outdated"] == OUTDATED_YES)
    ]
