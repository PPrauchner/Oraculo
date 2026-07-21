"""
Normalizes and structures declared dependencies.

Receives the processed output of readers.py (a list of dicts with Package, Used Version
and Origin) and returns a standardized list with the complete structure including:
- Package
- Used Version
- PyPI Version (initially "N/A")
- Status (initially Indeterminate — before PyPI there is no status to assert)
- Origin (Production when not informed)

Input:
- List of dictionaries processed by readers.py

Output:
- Standardized list of dictionaries with the complete structure
"""

from typing import Dict, List, Optional
from utils.constants import ORIGIN_PRODUCTION, STATUS_UNKNOWN
from utils.types import DeclarationEntry, Dependency
from utils.functions import READERS
from core.ingestion.filter import is_path_in_ignored_folders

def normalize_dependency(dep: DeclarationEntry) -> Optional[Dependency]:
    """
    Normalizes an individual dependency dictionary.

    Receives a dict with 'Package' and 'Used Version' and returns a
    standardized dict with all the required fields.

    The Origin is preserved: it is what allows exempting Development
    Dependencies from the Zombie classification (ADR-0003). In its absence,
    Production is assumed — the conservative choice.

    Args:
        dep: Dictionary with 'Package', 'Used Version' and, optionally, 'Origin'

    Returns:
        Standardized dictionary or None if invalid
    """
    if not isinstance(dep, dict):
        return None

    # Validate required fields
    pacote = dep.get("package", "").strip()
    versao_usada = dep.get("used_version", "").strip()

    if not pacote:
        return None

    return {
        "package": pacote,
        "used_version": versao_usada,
        "pypi_version": "N/A",
        "status": STATUS_UNKNOWN,
        "origin": dep.get("origin", ORIGIN_PRODUCTION),
    }


def parse_dependencies(dependencies: List[DeclarationEntry]) -> List[Dependency]:
    """
    Processes a list of dependencies and returns a standardized list.

    Receives the output of readers.py (parse_requirements or parse_uv_lock)
    and returns a list of dependencies with a standardized structure.

    Args:
        dependencies: List of dicts with 'Package' and 'Used Version'

    Returns:
        Standardized list of dictionaries with fields: Package, Used Version, PyPI Version, Status
    """
    if not dependencies:
        return []

    if not isinstance(dependencies, list):
        return []

    normalized = []
    for dep in dependencies:
        normalized_dep = normalize_dependency(dep)
        if normalized_dep:
            normalized.append(normalized_dep)

    return normalized


def parse_dependencies_with_filter(
    dependencies: List[DeclarationEntry], file_path: str, ignore_folders: List[str]
) -> List[Dependency]:
    """
    Processes dependencies with a filter by ignored folder.

    If the source file is in an ignored folder, returns an empty list.
    Otherwise, processes and returns the normalized dependencies.

    Args:
        dependencies: List of dicts with 'Package' and 'Used Version'
        file_path: Path of the source file (e.g.: "tests/requirements.txt")
        ignore_folders: List of folders to ignore (e.g.: ["tests", "docs"])

    Returns:
        Empty list if the file is in an ignored folder, otherwise the normalized list
    """
    

    if is_path_in_ignored_folders(file_path, ignore_folders):
        return []

    return parse_dependencies(dependencies)
