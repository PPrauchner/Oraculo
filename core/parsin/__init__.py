"""
parsin module - Reading, parsing and normalization of dependencies.

Combines:
- readers.py: Extracts raw data from requirements.txt and .lock files
- dependency_parser.py: Normalizes and structures the dependencies
- declaration_collector.py: Merges the Declarations into the audited set (Lock left out)
- import_parser.py: Identifies imports used in the source code
- normalization.py: Resolves differences between package and import names
"""

from .readers import parse_requirements, parse_lock, parse_environment_yml
from .dependency_parser import (
    parse_dependencies,
    normalize_dependency,
    parse_dependencies_with_filter,
)
from .declaration_collector import collect_declarations
from .import_parser import parse_imports, parse_imports_with_filter

__all__ = [
    "parse_requirements",
    "parse_lock",
    "parse_environment_yml",
    "parse_dependencies",
    "normalize_dependency",
    "parse_dependencies_with_filter",
    "collect_declarations",
    "parse_imports",
    "parse_imports_with_filter",
]
