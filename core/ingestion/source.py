"""
The Target Project's file source, reduced to two primitives.

Responsibilities:
- List the Target Project paths, relative to its root (`list_paths`).
- Read a file's content by path (`read_text`).
- Open a local directory as a source, with an error code (`open_directory`).

The only module in the project allowed to know `ZipFile`/`TarFile`: the `isinstance`
dispatch stays confined here (ADR-0006). Consumers ask for path and content,
and for that reason it works the same in the two ingestion modes of ADR-0001.

**Reading by path, and not by member, is what kills the coupling**: as long as the read
asked for a `ZipInfo`/`TarInfo`, the type leaked to the caller. Laziness is preserved
— walking the index is cheap, decoding each file is not, so `read_text` is only
called for what passed the filter.

Size and Age do **not** belong in the contract: they come from PyPI, not from disk (ADR-0004).
"""

import os
import tarfile
import zipfile
from pathlib import Path
from weakref import WeakKeyDictionary

# The kinds of source the dispatch recognizes (ADR-0006). `dict` maps path to
# content and serves as a stand-in in tests, without building a real archive.
ProjectSource = zipfile.ZipFile | tarfile.TarFile | Path | dict[str, str]

# How `core/ingestion/` rejects a Target Project: a stable English code plus the
# data that describes it (ADR-0010). The code does not change with the screen language —
# translating and choosing an icon is a decision of whoever renders, not of whoever
# detects the problem.
IngestionError = tuple[str, dict[str, str]]

# Folders that are never part of the Target Project: virtual environment, tool
# cache and VCS metadata. A directory on disk carries them and an archive
# usually does not; ignoring them on both sides is what makes directory and ZIP
# audit the same Target Project (ADR-0001).
NON_PROJECT_FOLDERS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "node_modules",
        ".idea",
        ".vscode",
        "site-packages",
    }
)

# Files that, at the root, give away a Python project
PROJECT_MARKERS = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "environment.yml",
        "environment.yaml",
        "pipfile",
    }
)


def _normalize(raw_path: str) -> str:
    """Standardizes a raw path coming from any kind of source.

    Args:
        raw_path: Path as the source delivers it, possibly with a Windows
            separator, a "./" prefix or a trailing slash.

    Returns:
        Path with "/" separator, without "./" prefix and without trailing slash. Empty
        string when nothing remains.
    """
    clean = raw_path.replace("\\", "/").strip("/")
    while clean.startswith("./"):
        clean = clean[2:]
    return clean


def _is_project_path(path: str) -> bool:
    """Indicates whether a path belongs to the Target Project, and not to the surrounding environment."""
    return not any(segment in NON_PROJECT_FOLDERS for segment in path.split("/"))


def _decode(data: bytes) -> str:
    """Decodes a file's content, standardizing the line ending.

    The same Target Project read from a directory on Windows would bring "\\r\\n" where the
    archive brings "\\n", and the residual "\\r" would enter the Distribution Name of a
    Declaration read line by line.

    Args:
        data: Raw bytes of the file.

    Returns:
        Text with invalid bytes discarded and line ending "\\n".
    """
    text = data.decode("utf-8", errors="ignore")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _looks_like_a_python_project(directory: Path) -> bool:
    """Indicates whether the directory root has a Python project marker.

    Looks only at the first level, on purpose: it is the cheap check that stops the
    ORÁCULO from walking a huge tree (the user's folder, an entire
    disk) before discovering there is no Target Project there at all.

    Args:
        directory: Directory pointed at by the user.

    Returns:
        True if there is, at the root, a .py file, a Declaration or a Lock.
    """
    with os.scandir(directory) as entries:
        for entry in entries:
            if not entry.is_file():
                continue

            name = entry.name.lower()
            if name in PROJECT_MARKERS or name.endswith((".py", ".lock")):
                return True
            if name.startswith("requirements") and name.endswith(".txt"):
                return True

    return False


def _project_root_prefix(paths: list[str]) -> str:
    """Discovers the folder that merely wraps the Target Project, if any.

    An archive usually contains everything inside a single root folder
    (`grupo-03-main/core/...`) — it is the format that GitHub's "Download ZIP" produces.
    In that case the Target Project root is inside it. The folder is only a wrapper if it
    is not, itself, a package.

    Args:
        paths: Already-normalized paths, relative to the source.

    Returns:
        The prefix to remove (with trailing "/"), or "" when there is no wrapper.
    """
    top_segments = {path.split("/")[0] for path in paths}
    if len(top_segments) != 1:
        return ""

    root = top_segments.pop()

    # A root that is a package (or a loose file) is not a wrapper
    if root.endswith(".py") or f"{root}/__init__.py" in paths:
        return ""

    # Every path must be inside it; otherwise the root is a top-level file
    if not all(path.startswith(f"{root}/") for path in paths):
        return ""

    return f"{root}/"


def _walk_directory(root: Path) -> list[str]:
    """Walks a directory returning the relative paths of the files.

    Prunes the folders that are not the Target Project during the descent, so as not
    to walk an entire `.venv` only to discard it afterwards.

    Args:
        root: Target Project root on disk.

    Returns:
        File paths, relative to `root`, with "/" separator.
    """
    paths = []

    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in NON_PROJECT_FOLDERS]
        for name in filenames:
            paths.append(Path(current, name).relative_to(root).as_posix())

    return paths


def _read_directory_file(root: Path, path: str) -> str | None:
    """Reads a file from a directory-based Target Project, without re-walking the tree.

    Args:
        root: Target Project root on disk.
        path: Path relative to the root.

    Returns:
        Decoded bytes of the file, or None if the path cannot be read or
        escapes the Target Project root.
    """
    clean = _normalize(path)

    if not clean or not _is_project_path(clean) or ".." in clean.split("/"):
        return None

    try:
        target = root / clean

        # `_normalize` strips the leading slash, but not the drive letter: in
        # `root / "C:/segredo.txt"` pathlib discards `root` and the path stands
        # on its own. Checking the containment after resolving is what upholds the
        # documented guarantee — no read outside the Target Project root.
        if not target.resolve().is_relative_to(root.resolve()):
            return None

        return _decode(target.read_bytes())
    except Exception:
        return None


def is_supported(source: object) -> bool:
    """Indicates whether the source is of a kind the dispatch knows how to open.

    Whoever validates the Target Project needs to distinguish "this source has no .py file"
    from "I do not know how to open this source": both produce an empty path list, but only
    the first is a diagnosis about the Target Project. The `isinstance` stays confined
    here (ADR-0006).

    Args:
        source: Candidate Target Project source.

    Returns:
        True if it is a ZipFile, TarFile, Path or dict.
    """
    return isinstance(source, (zipfile.ZipFile, tarfile.TarFile, Path, dict))


def _raw_paths(source: ProjectSource) -> list[str]:
    """Lists the raw file paths of a source, without normalizing.

    Directory entries are not files and are left out.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).

    Returns:
        Paths as the source records them. Empty if the kind is not supported.
    """
    if isinstance(source, zipfile.ZipFile):
        return [info.filename for info in source.infolist() if not info.is_dir()]

    if isinstance(source, tarfile.TarFile):
        return [member.name for member in source.getmembers() if member.isfile()]

    if isinstance(source, Path):
        return _walk_directory(source)

    if isinstance(source, dict):
        return list(source)

    return []


def _build_index(source: ProjectSource) -> dict[str, str]:
    """Maps each path relative to the Target Project root to the source's raw path.

    It is what lets `read_text` receive a `str` from the caller and still find the
    right member inside the archive, including when there is a wrapper folder.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).

    Returns:
        Map of path relative to the root -> raw path.
    """
    normalized: dict[str, str] = {}

    for raw in _raw_paths(source):
        clean = _normalize(raw)
        if clean and _is_project_path(clean):
            normalized[clean] = raw

    # The directory pointed at by the user is already the root: nothing to peel off.
    if isinstance(source, Path):
        return normalized

    prefix = _project_root_prefix(list(normalized))
    if not prefix:
        return normalized

    return {
        path[len(prefix) :]: raw
        for path, raw in normalized.items()
        if path.startswith(prefix)
    }


# The already-built index of each archive. An archive is opened over in-memory bytes and
# does not change while it exists, so the index is valid for its whole lifetime; the entry
# disappears when the archive is collected (a new upload does not accumulate with the previous one).
#
# The directory is left out on purpose, and not by oversight: it is mutable on disk
# and may change between two Streamlit reruns, so a memoized index would serve stale
# data. Re-walking is the price of the correct answer.
_ARCHIVE_INDEX: WeakKeyDictionary = WeakKeyDictionary()


def _index(source: ProjectSource) -> dict[str, str]:
    """The source's index, built once per archive.

    `read_text` is called once per file that passes the filter. Without memoizing,
    reading N files from an archive would cost N sweeps of the whole index — the same
    O(n²) that `_read_directory_file` already avoids on the directory side.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).

    Returns:
        Map of path relative to the root -> raw path.
    """
    if not isinstance(source, (zipfile.ZipFile, tarfile.TarFile)):
        return _build_index(source)

    cached = _ARCHIVE_INDEX.get(source)
    if cached is None:
        cached = _build_index(source)
        _ARCHIVE_INDEX[source] = cached

    return cached


def list_paths(source: ProjectSource) -> list[str]:
    """Lists the Target Project files, relative to its root.

    The order is alphabetical, not the source's: the same Target Project must produce
    the same report whether it comes from a directory or an archive, and the Origin of a
    package declared twice is that of the first occurrence.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).

    Returns:
        Paths with "/" separator, relative to the Target Project root, sorted.
        Empty if the source kind is not supported.
    """
    return sorted(_index(source))


def read_text(source: ProjectSource, path: str) -> str | None:
    """Reads a Target Project file as text, by path.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).
        path: Path relative to the Target Project root, as returned by
            `list_paths`.

    Returns:
        The file content, with invalid bytes discarded, or None if the path
        does not exist in the source or cannot be read.
    """
    # In a directory the path is already the path: resolving directly avoids re-walking
    # the whole tree for each file read, which is what `_index` would cost here.
    if isinstance(source, Path):
        return _read_directory_file(source, path)

    raw = _index(source).get(path)
    if raw is None:
        return None

    try:
        if isinstance(source, zipfile.ZipFile):
            data = source.read(raw)
        elif isinstance(source, tarfile.TarFile):
            extracted = source.extractfile(raw)
            if extracted is None:
                return None
            data = extracted.read()
        elif isinstance(source, dict):
            return source[raw]
        else:
            return None
    except Exception:
        return None

    return _decode(data)


def open_directory(path: str) -> tuple[Path | None, IngestionError | None]:
    """Opens a local directory as the Target Project source.

    Validates existence, type, read permission and the Python project marker at the
    root. The last is what prevents pointing at the user's folder and expecting the
    ORÁCULO to walk the entire disk before complaining; the audit of the
    minimum requirements, that one being complete, is left to `validate_project_structure`.

    Args:
        path: Path typed by the user.

    Returns:
        Pair (source, error). On success, the directory Path and None. On failure, None
        and the `IngestionError` that describes the rejection — the caller chooses icon,
        formatting and language (ADR-0010).
    """
    cleaned = path.strip().strip('"').strip("'")
    if not cleaned:
        return None, ("empty_path", {})

    directory = Path(cleaned).expanduser()

    if not directory.exists():
        return None, ("directory_not_found", {"path": str(directory)})

    if not directory.is_dir():
        return None, ("path_is_not_a_directory", {"path": str(directory)})

    try:
        is_project = _looks_like_a_python_project(directory)
    except PermissionError:
        return None, ("directory_not_readable", {"path": str(directory)})
    except OSError as error:
        return None, ("directory_read_failed", {"reason": str(error)})

    if not is_project:
        return None, ("not_a_python_project", {"path": str(directory)})

    return directory, None
