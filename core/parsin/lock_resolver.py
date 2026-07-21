"""
Resolves the Used Version of each package in the set from the Lock.

Responsibilities:
- Read the Target Project's Lock (uv.lock, poetry.lock), when present, and map each
  normalized Distribution Name to its exact version.
- Overwrite the Used Version of the packages already in the audited set with the
  Lock version, matching by normalized Distribution Name.

The Lock resolves versions, it does not define the set (ADR-0002): packages that exist only
in the Lock (transitive ones) do not enter the set — they only lend their version to those already
in it. That is why the resolution walks the set, never the Lock.
"""

from core.analysis.name_matching import normalize_name
from core.ingestion.archive_walker import iter_archive_texts
from core.parsin.declaration_collector import is_lock_filename
from core.parsin.readers import parse_lock


from utils.types import Dependency

def build_lock_version_map(archive, ignore_folders: list[str]) -> dict[str, str]:
    """Maps normalized Distribution Name to the exact version recorded in the Lock.

    Reads each Lock outside the Exclusions and accumulates its versions. The map also includes
    the transitive packages from the Lock; filtering what belongs to the set is the responsibility of
    `resolve_used_versions`.

    Args:
        archive: zipfile.ZipFile or tarfile.TarFile object of the Target Project.
        ignore_folders: Folders in Exclusion (e.g.: ["tests", "docs"]).

    Returns:
        Map of normalized Distribution Name -> exact version. Empty if there is no
        Lock outside the Exclusions.
    """
    version_map: dict[str, str] = {}

    for _path, content in iter_archive_texts(archive, ignore_folders, is_lock_filename):
        for entry in parse_lock(content):
            version = entry.get("used_version", "")
            if version:
                version_map[normalize_name(entry["package"])] = version

    return version_map


def resolve_used_versions(
    declared: list[Dependency], lock_version_map: dict[str, str]
) -> list[Dependency]:
    """Resolves the Used Version of each package in the set with the Lock version.

    For each package already in the set, if the Lock records its version (matching by
    normalized Distribution Name), that version becomes the Used Version, even if the
    Declaration carried a pin. Packages absent from the Lock keep what the Declaration
    resolved (pin or undefined). No package is added to the set (ADR-0002).

    Args:
        declared: Audited set (union of the Declarations), normalized.
        lock_version_map: Map of normalized Distribution Name -> Lock version.

    Returns:
        The same set, with the Used Version resolved where the Lock knows it.
    """
    for dep in declared:
        version = lock_version_map.get(normalize_name(dep["package"]))
        if version:
            dep["used_version"] = version

    return declared
