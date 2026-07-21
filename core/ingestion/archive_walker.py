"""
Walks the Target Project delivering the contents of the files that matter.

Responsibilities:
- Iterate the Target Project paths, whether it is an archive or a directory.
- Discard what is in an Exclusion and what the caller did not ask for.
- Read as text only the files that passed the filter.

Derives from the two primitives of `core.ingestion.source` (ADR-0006) instead of
reimplementing them: whoever reads Declarations and the Lock asks for path + content
and does not know the kind of source.
"""

from typing import Callable, Iterator

from core.ingestion.filter import is_path_in_ignored_folders
from core.ingestion.source import ProjectSource, list_paths, read_text


def iter_archive_texts(
    source: ProjectSource, ignore_folders: list[str], keep: Callable[[str], bool]
) -> Iterator[tuple[str, str]]:
    """Walks the Target Project and yields (path, content) of the requested files.

    Only the files approved by `keep` are read: walking the source index is
    cheap, decoding each file is not.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).
        ignore_folders: Folders in Exclusion (e.g.: ["tests", "docs"]).
        keep: Decides, by the path, whether the file matters to the caller.

    Yields:
        (path, content) pairs of the files outside the Exclusions that `keep`
        approved and that could be read as text.
    """
    for file_path in list_paths(source):
        if is_path_in_ignored_folders(file_path, ignore_folders):
            continue

        if not keep(file_path):
            continue

        content = read_text(source, file_path)
        if content is None:
            continue

        yield file_path, content
