"""
Format of the records that flow through the audit pipeline.

Responsibilities:
- Describe the audited Dependency, as `parsin` produces it and `analysis` enriches it.
- Describe the row displayed in the report and the export row, which derive from it.

ADR-0011 introduces these `TypedDict`s as a safety net for the renaming of the keys to
English (ADR-0008): in a schemaless `dict`, a mistyped key does not fail at the
moment — `.get()` returns the default and the report comes out empty, with no error and no warning.
Once the format is declared, the type checker demands each read point.

At runtime this remains a plain `dict`: no instantiation, no `self`,
no method. No business rule lives here — the one that classifies Zombie is
`zombie_analizer`, the one that computes Age is `pypi_client`. Rule 01 (procedural
paradigm) forbids modeling the domain in objects with state and behavior, and
`TypedDict` uses `class` as type-declaration syntax, not as a constructor:
it is erased at runtime and exists only for the type checker.

The `CONTEXT.md` glossary bridges the domain term in Portuguese and the
identifier here — Pacote is `package`, Versão Usada is `used_version`. The label
the user reads in the CSV is a third vocabulary, and lives in `CSV_HEADER`.
"""

from typing import NotRequired, TypedDict

# Size and Age come out raw (bytes, days) from PyPI, or as the unavailability
# sentinel when the Used Version was not resolved (ADR-0002/ADR-0004).
RawMetric = int | str


class DeclarationEntry(TypedDict):
    """What a reader extracts from a Declaration, before it becomes a Dependency.

    Smaller than the Dependency on purpose: the Declaration says the Package and, when
    it fixes a version, the Used Version. `pypi_version` and `status` only exist after
    querying PyPI, and declaring them here would promise a field that the reader never
    fills.
    """

    package: str
    # Empty when the Declaration does not fix a version — an exact pin is the only one that
    # defines the Used Version (ADR-0002), and the Lock resolves the rest afterwards.
    used_version: str
    # Filled by the readers that distinguish a development group; it is what
    # exempts the Development Dependency from becoming a Zombie (ADR-0003).
    origin: NotRequired[str]


class Dependency(TypedDict):
    """The audited Dependency, as it flows from `parsin` to the report."""

    package: str
    used_version: str
    pypi_version: str
    status: str
    # Filled by `analysis` from PyPI, absent until then.
    size: NotRequired[RawMetric]
    age: NotRequired[RawMetric]
    # A Ghost has no Declaration, so it has no Origin (CONTEXT.md).
    origin: NotRequired[str]


class ReportRow(TypedDict):
    """The row that feeds the report table, as it leaves `normalize`.

    It carries data and identity, not text: the one who chooses unit, wording and language is
    `utils/display.py` (ADR-0010). While `normalize` returned "30 dias" ready-made,
    the table answered in Portuguese under `?lang=en` and there was nothing left to translate.
    """

    package: str
    used_version: str
    pypi_version: str
    # Stable identity (`STATUS_*`), not label — it is also compared.
    status: str
    # Raw, as in the export: bytes and whole days, or the Indeterminate.
    size: RawMetric
    age: RawMetric
    origin: str
    # Whether Size and Age refer to the most recent version on PyPI instead of the Used
    # Version — the case of the Ghost, which has no Declaration. The table makes this explicit;
    # without the note, it would claim about the running version a number that describes another.
    metrics_from_latest: bool


class CategorySummary(TypedDict):
    """The aggregations of a Category, as `summarize_category` produces them.

    It was left out of the ADR-0008 renaming because it does not touch the CSV nor describe a
    dependency — but it is a record that flows through `core/report/` to the screen, and the same
    argument of ADR-0011 applies: a mistyped key in a loose `dict` returns the
    default and the metric comes out empty, with no error and no warning.

    `None` in `total_size`/`average_age` is not zero: it means that no
    dependency of the category had the metric measured, and summing or averaging the
    Indeterminate as 0 would invent a number that PyPI did not give (ADR-0004).
    """

    count: int
    total_size: float | None
    average_age: float | None
    # How many were left out of each aggregation, so the average does not mislead the reader.
    missing_size: int
    missing_age: int


class SummaryMetric(TypedDict):
    """One of the statistics of a Category, before it becomes a caption.

    `format_summary_lines` used to return "Tamanho: 1.2 MB (1 de 2 sem dado)" — a
    ready-made phrase, in Portuguese, produced inside `core/`. This is the pair that ADR-0010
    asks for instead: the metric's identity and the data that describe it, with the
    wording left to `utils/display.py`.
    """

    # "size" or "age": stable identity, not label.
    metric: str
    # `None` when no dependency of the category had the metric measured.
    value: float | None
    # How many were left out, and out of how many — an average computed over half the
    # packages, without warning, misleads the reader.
    missing: int
    total: int


class ExportRow(TypedDict):
    """The CSV row, as it leaves `build_export_rows`.

    The declaration order is the order of the file's columns (ADR-0008), and the
    labels the user reads come from `CSV_HEADER` — never from these keys.
    """

    analysis_date: str
    project: str
    package: str
    category: str
    origin: str
    used_version: str
    pypi_version: str
    # Outdated is its own column, and not a Category value: a dependency
    # can be a Zombie *and* Outdated, and a single field would lose one of the readings.
    outdated: str
    # Raw, never formatted: the CSV is for diffing and concatenation over
    # time, not for direct human reading — that is `normalize`.
    size: RawMetric
    age: RawMetric
