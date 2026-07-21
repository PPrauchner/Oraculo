"""
Gathers the audited set from the union of all Declarations.

Responsibilities:
- Walk the Target Project and read each Declaration outside the Exclusions.
- Merge the declared packages, deduplicating by Distribution Name.
- Leave the Lock out of the set: it resolves versions, it does not define it (ADR-0002).

The Lock (uv.lock, poetry.lock) lists hundreds of transitive packages that nobody imports;
reading it as a Declaration would make every transitive one a Zombie. That is why the set
comes only from the Declarations; the Lock enters later, to resolve the Used Version.
"""

from typing import Callable, Dict, List

from utils.constants import LOCK_EXTENSION
from utils.functions import READERS
from utils.types import Dependency
from core.ingestion.archive_walker import iter_archive_texts
from core.parsin.dependency_parser import parse_dependencies

# Populate the READERS registry: the `registrar` decorator only runs when the module
# is imported (see utils/functions.py).
import core.parsin.readers  # noqa: F401


def is_lock_filename(file_name: str) -> bool:
    """Indicates whether a file is a Lock (uv.lock, poetry.lock).

    The Lock resolves versions, it does not define the audited set (ADR-0002), so it is
    ignored when building the set.

    Args:
        file_name: File name or path.

    Returns:
        True if the file is a Lock, False otherwise.
    """
    return file_name.lower().endswith(LOCK_EXTENSION)


def _match_declaration_reader(file_name: str) -> Callable[[str], list] | None:
    """Returns the reader of a Declaration, or None if the file is not one.

    The Lock matches the `.lock` reader, but it never defines the set (ADR-0002), so it
    is discarded before consulting the registry.

    Args:
        file_name: File name or path.

    Returns:
        The reading function registered for the Declaration, or None.
    """
    lower = file_name.lower()
    if is_lock_filename(lower):
        return None

    for extension, reader in READERS.items():
        if lower.endswith(extension):
            return reader
    return None


def _is_declaration(file_name: str) -> bool:
    """Indicates whether a file is a Declaration that some reader knows how to read."""
    return _match_declaration_reader(file_name) is not None


def merge_declarations(dependencies: List[Dependency]) -> List[Dependency]:
    """Merges Declarations, deduplicating by Distribution Name.

    A package declared in more than one Declaration appears a single time, with the
    Origin of the first occurrence preserved (ADR-0002).

    Args:
        dependencies: Normalized dependencies, possibly with repetitions.

    Returns:
        List without duplicates, in the order of the first occurrence of each package.
    """
    seen = set()
    merged = []
    for dep in dependencies:
        key = dep["package"].lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(dep)
    return merged


def collect_declarations(archive, ignore_folders: List[str]) -> List[Dependency]:
    """Builds the audited set as the union of all Declarations.

    For each Declaration outside the Exclusions, accumulates its packages. The Lock is
    ignored (ADR-0002). The result is deduplicated by Distribution Name, preserving the
    Origin of each package.

    Args:
        archive: zipfile.ZipFile or tarfile.TarFile object of the Target Project.
        ignore_folders: Folders in Exclusion (e.g.: ["tests", "docs"]).

    Returns:
        The audited set as a list of normalized dependencies. Empty if the
        Target Project has no Declaration outside the Exclusions.
    """
    declared: List[Dependency] = []

    for file_path, content in iter_archive_texts(
        archive, ignore_folders, _is_declaration
    ):
        reader = _match_declaration_reader(file_path)
        declared.extend(parse_dependencies(reader(content)))

    return merge_declarations(declared)
