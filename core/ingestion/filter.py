"""
Applies the Exclusions and checks the Target Project's minimum requirements.

Responsibilities:
- Offer the Target Project folders that can become an Exclusion.
- Decide whether a path is inside an Exclusion.
- Validate that the Target Project has Python code and at least one Declaration.

Works over paths coming from `core.ingestion.source`, and for that reason applies
equally to archive and to directory (ADR-0001). An Exclusion is a **folder name**, and
matches at any depth: marking `tests` excludes `tests/` and `src/tests/`.
"""

from core.ingestion.source import (
    IngestionError,
    ProjectSource,
    is_supported,
    list_paths,
)


def _folder_name(folder: str) -> str:
    """Reduces an Exclusion to the folder name, tolerating `./tests/` and `.\\tests`."""
    return folder.replace("\\", "/").strip("/").removeprefix("./").strip()


def get_unique_folders(source: ProjectSource) -> list[str]:
    """Lists the Target Project folders that can become an Exclusion.

    Every folder returned here is excludable by `is_path_in_ignored_folders`: the two
    functions speak of the same thing — folder name at any depth. It was the
    divergence between them that made the UI offer Exclusions with no effect (issue #26).

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).

    Returns:
        Folder names, without repetition, in alphabetical order.
    """
    folders = set()

    for path in list_paths(source):
        # The last segment is the file, not a folder
        folders.update(path.split("/")[:-1])

    return sorted(folders)


def is_path_in_ignored_folders(file_path: str, ignore_folders: list[str]) -> bool:
    """Indicates whether a path is inside some Exclusion.

    Matches by segment, at any depth: marking `tests` excludes both
    `tests/test_x.py` and `src/tests/test_x.py`. A file whose name matches
    the Exclusion is not excluded — an Exclusion is a folder.

    Args:
        file_path: File path, relative to the Target Project root.
        ignore_folders: Folders in Exclusion (e.g.: ["tests", "docs"]).

    Returns:
        True if the file is in an Exclusion, False otherwise.
    """
    if not ignore_folders or not file_path:
        return False

    parent_segments = set(file_path.replace("\\", "/").strip("/").split("/")[:-1])
    excluded_names = {_folder_name(folder) for folder in ignore_folders}

    return not excluded_names.isdisjoint(parent_segments)


def should_skip_file(file_path: str, ignore_folders: list[str]) -> bool:
    """
    Checks whether a file should be ignored.

    Args:
        file_path: File path
        ignore_folders: List of folders to ignore

    Returns:
        True if the file should be ignored, False otherwise
    """
    return is_path_in_ignored_folders(file_path, ignore_folders)


def validate_project_structure(
    source: ProjectSource, ignore_folders: list[str] | None = None
) -> tuple[bool, IngestionError | None]:
    """Validates whether the Target Project has the minimum requirements for the audit.

    Requires, outside the Exclusions, at least one `.py` file and at least one
    Declaration (or Lock). Applies equally to archive and to directory, so the
    error codes do not mention file format.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).
        ignore_folders: Folders in Exclusion (e.g.: ["tests", "docs"]).

    Returns:
        Pair (is_valid, error). On success, (True, None); on failure, the
        `IngestionError` that describes what is missing (ADR-0010).
    """
    if source is None:
        return False, ("source_missing", {})

    # A source the dispatch cannot open produces an empty path list, indistinguishable
    # from a Target Project without code. Without this early return, the user would hear
    # that .py files are missing from a Target Project that was never even read.
    if not is_supported(source):
        return False, ("unsupported_source", {})

    if ignore_folders is None:
        ignore_folders = []

    DEPENDENCY_EXTENSIONS = (
        "requirements.txt",
        ".lock",
        "pyproject.toml",
        "environment.yml",
    )

    has_python_files = False
    has_dependency_file = False

    try:
        for file_path in list_paths(source):
            if is_path_in_ignored_folders(file_path, ignore_folders):
                continue

            file_lower = file_path.lower()

            if file_lower.endswith(".py"):
                has_python_files = True

            if file_lower.endswith(DEPENDENCY_EXTENSIONS):
                has_dependency_file = True

            if has_python_files and has_dependency_file:
                return True, None

    except Exception as e:
        return False, ("project_read_failed", {"reason": str(e)})

    if not has_python_files and not has_dependency_file:
        return False, ("missing_python_and_declaration", {})
    elif not has_python_files:
        return False, ("missing_python_files", {})
    else:
        return False, ("missing_declaration", {})
