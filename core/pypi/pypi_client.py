"""
Communication with the public PyPI API.

Responsibilities:
- Fetch, in a single request to `/pypi/NAME/json`, a package's metadata.
- Extract from that same response the most recent version, the Size and the Age of a
  specific version (ADR-0004), without new requests.
"""

from datetime import date, datetime

import requests

from utils.constants import PYPI_BASE_URL

_TIMEOUT_SECONDS = 5

# The fetches run in parallel (32 threads). A shared Session keeps the
# connection pool alive between them, saving the TLS handshake for each package.
_SESSION = requests.Session()


def fetch_package_data(package_name: str) -> dict | None:
    """Fetches a package's metadata from PyPI in a single request.

    Args:
        package_name: Distribution Name of the package (e.g.: "pandas").

    Returns:
        The already-parsed JSON of `/pypi/NAME/json`, or ``None`` when the package does
        not exist on PyPI (private/internal) or there is a network failure — without breaking the
        analysis of the other packages.
    """
    url = f"{PYPI_BASE_URL}/{package_name}/json"

    try:
        response = _SESSION.get(url, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        print(f"Não foi possível checar o pacote '{package_name}' no PyPI. ({error})")
        return None


def get_latest_version(data: dict) -> str:
    """Extracts the most recent version from the already-fetched metadata.

    Args:
        data: Metadata already fetched via `fetch_package_data`.

    Returns:
        The published version, or "" when the response does not bring it — a malformed
        response is unavailability of a package, not a reason to abort the
        analysis of the others.
    """
    return data.get("info", {}).get("version", "")


def _release_files(data: dict, version: str) -> list[dict]:
    """Published files of a version (empty if the version does not exist)."""
    return data.get("releases", {}).get(version, [])


def get_release_size(data: dict, version: str) -> int | None:
    """Size in bytes of a version: the wheel's bytes, with sdist as fallback.

    Args:
        data: Metadata already fetched via `fetch_package_data`.
        version: Exact version whose Size is wanted (the Used Version).

    Returns:
        The bytes of a wheel (`bdist_wheel`); in the absence of a wheel, those of the sdist;
        ``None`` when the version has no artifacts or does not exist in the response.

    A package with per-platform wheels publishes dozens of artifacts of the same
    version, of quite different sizes. The choice is fixed by the alphabetical order of the
    file name, not by the order in which PyPI returned them: ADR-0004 requires that the
    same package always give the same number, otherwise the US-07 time series invents
    variation that never happened.
    """
    files = _release_files(data, version)
    if not files:
        return None

    wheels = [f for f in files if f.get("packagetype") == "bdist_wheel"]
    sdists = [f for f in files if f.get("packagetype") == "sdist"]
    candidates = wheels or sdists or files
    chosen = min(candidates, key=lambda f: f.get("filename", ""))

    return chosen.get("size")


def _parse_upload_time(raw: str) -> date | None:
    """Converts PyPI's `upload_time` (ISO, naive UTC) into a date."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "")).date()
    except ValueError:
        return None


def get_release_age_days(
    data: dict, version: str, today: date | None = None
) -> int | None:
    """Age in days of a version: today minus its publication date.

    The version's publication date is the oldest `upload_time` among its
    artifacts (ADR-0004).

    Args:
        data: Metadata already fetched via `fetch_package_data`.
        version: Exact version whose Age is wanted (the Used Version).
        today: Reference date; uses `date.today()` when omitted.

    Returns:
        Whole days since publication, or ``None`` when the version does not exist
        or does not bring `upload_time`.
    """
    files = _release_files(data, version)
    upload_dates = [
        parsed
        for f in files
        if (parsed := _parse_upload_time(f.get("upload_time", ""))) is not None
    ]
    if not upload_dates:
        return None

    reference = today or date.today()
    return (reference - min(upload_dates)).days
