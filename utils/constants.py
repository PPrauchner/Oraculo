"""
Application constants module.

Defines fixed values and configuration used throughout the application,
such as themes, colors, fonts and other style parameters.
"""

# ============ Colors =================#
# No color is defined here. The palette is single and lives in `.streamlit/config.toml`;
# this module only says *which token* each Category uses, and `utils/theme.py` resolves the
# token into the color. Keeping the hex in both places is what made the palette diverge —
# there were three different blues before (issue #39).

import sys


# Category (stable identity, as `pages/report.py` names it) -> semantic token
# of the theme. Streamlit already adapts these tokens to both backgrounds, so the Category does
# not need to know whether the screen is light or dark.
#
# The key is the identity, not the label: the label changes with the language (ADR-0009) and the
# color of a Category cannot depend on the language in which the screen is open.
STATUS_COLOR_TOKENS = {
    "healthy": "greenColor",  # Healthy
    "zombies": "violetColor",
    "ghosts": "redColor",
    "outdated": "blueColor",
}
# ============ Colors =================#

# The magnifying glass inherits the color of its container (`stroke="currentColor"`), so it follows the
# theme without carrying its own color.
SVG_LUPA = """
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" transform="scale(-1, 1)" transform-origin="center" style="margin-right: 10px; vertical-align: middle;">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    </svg>
    """

PYPI_BASE_URL = "https://pypi.org/pypi"

# ============ Origin =================#
# From which Declaration — and from which section of it — a package came. Separates
# Production Dependency from Development Dependency (see CONTEXT.md and ADR-0003).

ORIGIN_PRODUCTION = "Production"
ORIGIN_DEVELOPMENT = "Development"
# A Ghost does not come from a Declaration, so it has no Origin: that is how it identifies itself
# in the report and in the export (see `is_ghost`).
ORIGIN_UNAVAILABLE = "N/A"
# ============ Origin =================#

# ============ Category =================#
# Classification of a dependency in the report/export. Derived from the analysis
# lists (Zombie, Ghost) — the rest of what is audited is Healthy. Outdated is NOT a
# Category: it is its own column, since a dependency can be a Zombie and Outdated at the
# same time (see CONTEXT.md and the US-06/US-07 issue).
CATEGORY_ZOMBIE = "Zombie"
CATEGORY_GHOST = "Ghost"
CATEGORY_HEALTHY = "Healthy"

# Marker of the Outdated column in the export (readable boolean).
OUTDATED_YES = "Yes"
OUTDATED_NO = "No"
# ============ Category =================#

# ============ Absence of value =================#
# Two absences the report cannot confuse (CONTEXT.md): one is a limit of what
# is known, the other a property of what was audited.
#
# Indeterminate — the ORÁCULO has no way to know. It is the Used Version without Lock and without pin
# and, consequently, the Size, the Age and the Status that depend on it. A Lock
# would resolve it. The Not Applicable ("N/A", `ORIGIN_UNAVAILABLE`) is the other: no extra
# file would fill the Origin of a Ghost, because it does not come from any Declaration.
UNKNOWN = "Unknown"
# ============ Absence of value =================#

# ============ Status =================#
# How the Used Version compares to the latest published on PyPI. It is stable identity,
# not label: `build_export_rows` and `pages/report.py` *compare* against these values
# to decide what is Outdated. Translating them along with the text would break the two
# comparisons in silence — the Outdated column would come out "No" for everyone and the
# Outdated tab, empty. The displayed label is resolved by `t()` at render time, the same pair
# that the Category already uses (ADR-0009/ADR-0010).
STATUS_OUTDATED = "Outdated"
STATUS_UP_TO_DATE = "Up to date"
STATUS_INVALID_VERSION = "Invalid version"
# The fourth value is the absence itself: not knowing the Used Version, or not getting
# a response from PyPI, is having no status to assert. An alias, not a repeated string, so
# that the two readings cannot diverge.
STATUS_UNKNOWN = UNKNOWN
# ============ Status =================#

# ============ Lock =================#
# Extension of the Lock files (uv.lock, poetry.lock). The Lock resolves versions,
# it does not define the audited set (ADR-0002).
LOCK_EXTENSION = ".lock"
# ============ Lock =================#

PYTHON_STDLIB_MODULES = getattr(sys, "stdlib_module_names", set())

# ============ Import Alias =================#
# Maps Distribution Name (normalized: lowercase and "-" -> "_") to the Import
# Names that the package exposes *beyond its own name* — `import_names_for` already
# adds the normalized name, so repeating it here is redundant. Without this table the
# same package becomes a Ghost and a Zombie at the same time (e.g.: PyYAML ↔ yaml). See
# CONTEXT.md (Import Alias) and the limitation documented in the README: packages outside this
# table still generate the pair of false positives.
#
# A shared namespace does not enter: mapping `protobuf` to `google` would make a project
# that imports `google.cloud.storage` "use" a declared and idle protobuf — a false
# negative in US-03, the inverse of what the table solves.
IMPORT_ALIASES: dict[str, list[str]] = {
    "pyyaml": ["yaml"],  # PyYAML
    "scikit_learn": ["sklearn"],  # scikit-learn
    "opencv_python": ["cv2"],  # opencv-python
    "opencv_python_headless": ["cv2"],  # opencv-python-headless
    "pillow": ["PIL"],  # Pillow
    "beautifulsoup4": ["bs4"],  # beautifulsoup4
    "python_dateutil": ["dateutil"],  # python-dateutil
    "python_dotenv": ["dotenv"],  # python-dotenv
    "python_docx": ["docx"],  # python-docx
    "python_pptx": ["pptx"],  # python-pptx
    "pycryptodome": ["Crypto"],  # pycryptodome
    "setuptools": ["pkg_resources"],  # exposes more than one Import Name
    "attrs": ["attr"],  # exposes more than one Import Name
}
# ============ Import Alias =================#
