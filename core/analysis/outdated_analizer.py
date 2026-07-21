"""
Identifies Outdated dependencies.

Compares the version used in the project against the most
recent version available on PyPI.

Input:
- List of dependencies with their current versions
- Data obtained from the PyPI API

Output:
- List of Outdated dependencies with their versions
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from core.analysis.ghost_analizer import is_ghost
from core.pypi.pypi_client import (
    fetch_package_data,
    get_latest_version,
    get_release_age_days,
    get_release_size,
)
from packaging.version import InvalidVersion, parse as parse_version
from utils.constants import (
    STATUS_INVALID_VERSION,
    STATUS_OUTDATED,
    STATUS_UNKNOWN,
    STATUS_UP_TO_DATE,
    UNKNOWN,
)
from utils.types import Dependency


def _used_version(dep: Dependency) -> str:
    """Returns the Used Version exactly as PyPI publishes it, or "" if unavailable.

    The Used Version already arrives resolved (Lock or exact pin), so there is no
    specifier to extract — and extracting would mangle a valid version: truncating the
    PEP 440 suffix would turn `2.0.0b1` into the key `2.0.0` and read the *wrong* release in
    `releases[]` (ADR-0004). The value is only accepted if it is a PEP 440 version; the "N/A"
    of a Ghost and the Indeterminate count as unavailable.

    Args:
        dep: Dependency with the 'used_version' key.

    Returns:
        The exact version, or "" when there is no known Used Version.
    """
    raw = (dep.get("used_version") or "").strip()

    try:
        parse_version(raw)
    except InvalidVersion:
        return ""

    return raw


def _set_size_and_age(dep: Dependency, data: dict, version: str | None) -> None:
    """Fills in 'Size' and 'Age' of the reference version from the metadata.

    Stores the raw values (bytes and whole days) or the unavailability
    sentinel; the human-readable formatting is left to the display layer.

    Args:
        dep: Dependency to fill in.
        data: Metadata already fetched from PyPI.
        version: Reference version (Used Version, or the most recent one for
            Ghosts). ``None`` when there is no reference (Indeterminate Used Version
            of a Declared Dependency): Size and Age stay that way, never 0.
    """
    if version is None:
        dep["size"] = UNKNOWN
        dep["age"] = UNKNOWN
        return

    size = get_release_size(data, version)
    age = get_release_age_days(data, version)
    dep["size"] = size if size is not None else UNKNOWN
    dep["age"] = age if age is not None else UNKNOWN


def _check_dependency(dep: Dependency) -> Dependency:
    """
    Queries PyPI for a single dependency (one request) and fills in
    'pypi_version', 'status', 'size' and 'age' directly into the dictionary.

    Called in parallel by the ThreadPoolExecutor.

    Args:
        dep: Dictionary with at least 'package' and 'used_version'.

    Returns:
        The same dictionary with 'pypi_version', 'status', 'size' and 'age'
        filled in.
    """
    data = fetch_package_data(dep["package"])
    used_version = _used_version(dep)
    pypi_version = get_latest_version(data) if data else ""

    if not pypi_version:
        # Package absent from PyPI (private/internal), network failure or a response with
        # no version: unavailable, without breaking the analysis of the other packages.
        dep["pypi_version"] = "N/A"
        dep["status"]      = STATUS_UNKNOWN
        if not used_version:
            # Same sentinel as the path with PyPI: not knowing the Used Version is
            # unavailability, regardless of whether the package exists on PyPI.
            dep["used_version"] = UNKNOWN
        _set_size_and_age(dep, data={}, version=None)
        return dep

    dep["pypi_version"] = pypi_version

    if not used_version:
        # Without Lock and without pin, the Used Version is unknown: we neither claim the
        # package is up to date nor copy the version from PyPI (ADR-0002). The Status is the
        # same absence as the metric — Indeterminate — and says so with the same word.
        dep["used_version"] = UNKNOWN
        dep["status"]       = STATUS_UNKNOWN
        # A Ghost has no Declaration, so it has no Origin (CONTEXT.md): it uses the
        # most recent version as the reference for Size/Age. A Declared
        # Dependency without a Used Version has no reference — it stays unavailable.
        _set_size_and_age(dep, data, pypi_version if is_ghost(dep) else None)
    else:
        _set_size_and_age(dep, data, used_version)
        try:
            if parse_version(used_version) < parse_version(pypi_version):
                dep["status"] = STATUS_OUTDATED
            else:
                dep["status"] = STATUS_UP_TO_DATE
        except Exception:
            dep["status"] = STATUS_INVALID_VERSION

    return dep


def analyze_dependency_status(dependencies: list[Dependency]) -> list[Dependency]:
    """
    Analyzes the status of each dependency by comparing against PyPI.

    Uses a ThreadPoolExecutor to fire the requests in parallel,
    reducing the execution time from sequential O(n) to near O(1)
    relative to the number of dependencies.

    Args:
        dependencies: List of dicts with 'package' and 'used_version'.

    Returns:
        The same list with 'pypi_version', 'status', 'size' and 'age'
        filled in on each item.
    """
    if not dependencies:
        return []

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(_check_dependency, dep): dep for dep in dependencies}

        for future in as_completed(futures):
            future.result()

    return dependencies