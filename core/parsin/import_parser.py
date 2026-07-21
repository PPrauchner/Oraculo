"""
Extracts imports from the source code.

Analyzes Python files using the AST (Abstract Syntax Tree)
to identify dependencies actually used in the code.

Input:
- Target Project source (archive or directory), via core.ingestion.source
- Folders in Exclusion

Output:
- List of dictionaries with the imports found:
  {
    "package": "module_name",
    "used_version": "N/A",
    "pypi_version": "N/A",
    "status": "Unknown"
  }
"""

import ast

from core.ingestion.filter import is_path_in_ignored_folders
from core.ingestion.source import ProjectSource, list_paths, read_text
from utils.constants import PYTHON_STDLIB_MODULES, STATUS_UNKNOWN
from utils.types import Dependency

# Folder that merely wraps the Own Modules in a `src/` layout
SRC_LAYOUT_FOLDER = "src"


def infer_own_modules(file_paths: list[str]) -> set[str]:
    """
    Infers the Own Modules from the Target Project layout.

    An Own Module is a package defined by the Target Project itself, recognizable
    by existing as a top-level folder with `__init__.py`. The inference uses only the
    paths already available from ingestion (archive or directory), with no extra I/O.

    Args:
        file_paths: Paths of the Target Project files, relative to its root.

    Returns:
        Set of Own Module names, in lowercase.
    """
    own_modules = set()

    for path in file_paths:
        parts = path.split("/")

        # In a `src/` layout, the Own Modules are the folders inside it
        if parts[0] == SRC_LAYOUT_FOLDER:
            parts = parts[1:]

        # Top-level folder with __init__.py: a Target Project package
        if len(parts) >= 2 and parts[1] == "__init__.py":
            own_modules.add(parts[0].lower())

        # Top-level .py file: a Target Project module
        elif len(parts) == 1 and parts[0].endswith(".py"):
            own_modules.add(parts[0][: -len(".py")].lower())

    return own_modules


def is_valid_import(module_name: str, own_modules: set[str] | None = None) -> bool:
    """
    Checks whether an import is valid for dependency analysis.

    Rejects:
    - Imports that start with an underscore (e.g.: _pytest, _internal)
    - Python native modules (stdlib)
    - Own Modules of the Target Project (never Ghosts)

    Args:
        module_name: Name of the imported module (in lowercase)
        own_modules: Own Modules inferred from the Target Project layout

    Returns:
        True if the import is valid, False otherwise
    """
    # Reject imports that start with an underscore
    if module_name.startswith("_"):
        return False

    # Reject Python native modules
    if module_name in PYTHON_STDLIB_MODULES:
        return False

    # Reject Own Modules: they belong to the Target Project, not to PyPI
    if own_modules and module_name in own_modules:
        return False

    return True


def _collect_imports_from_tree(
    tree: ast.AST, imports: set[str], own_modules: set[str] | None
) -> None:
    """
    Collects the valid Root Imports of an AST into the accumulator set.

    Walks the entire tree (not only the top), so indented imports — inside
    `try:`, functions, `if`, `with` — are also collected.

    Args:
        tree: AST of the code (or of an isolated line, in the fallback).
        imports: Accumulator set, altered in-place with the Root Imports.
        own_modules: Own Modules inferred from the Target Project layout.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0].lower()
                if is_valid_import(root_module, own_modules):
                    imports.add(root_module)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:  # Ignore relative imports
                root_module = node.module.split(".")[0].lower()
                if is_valid_import(root_module, own_modules):
                    imports.add(root_module)


def extract_imports_from_code(code: str, own_modules: set[str] | None = None) -> set[str]:
    """
    Extracts imported module names from Python code.

    Analyzes the code using the AST and extracts:
    - import xxx
    - from xxx import yyy
    - from xxx.yyy import zzz

    Normalizes to the root package name (e.g.: "django.core" → "django")
    Filters out invalid imports (start with _, stdlib modules, Own Modules)

    Args:
        code: Python code as a string
        own_modules: Own Modules inferred from the Target Project layout

    Returns:
        Set of unique module names
    """
    imports = set()

    try:
        # Normal case: the file is valid Python; a parse of the whole file
        # sees imports at any indentation level.
        _collect_imports_from_tree(ast.parse(code), imports, own_modules)
    except SyntaxError:
        # Fallback for a non-parseable file (e.g.: Python 2): recovers what it can,
        # line by line, saving imports before the first syntax error.
        for line in code.split("\n"):
            try:
                _collect_imports_from_tree(ast.parse(line), imports, own_modules)
            except SyntaxError:
                continue

    return imports


def parse_imports(
    source: ProjectSource, ignore_folders: list[str]
) -> list[Dependency]:
    """
    Extracts the Root Imports of all the Target Project's Python files.

    Iterates over the Python files, respects the Exclusions, extracts imports and returns
    a standardized list.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).
        ignore_folders: Folders in Exclusion (e.g.: ["tests", "docs"]).

    Returns:
        List of dictionaries with the imports found
    """
    if source is None:
        return []

    all_imports = set()

    # The paths already come relative to the Target Project root, so the Own
    # Modules come from the layout, with no extra I/O.
    file_paths = list_paths(source)
    own_modules = infer_own_modules(file_paths)

    for file_path in file_paths:
        # Check whether the file is in an Exclusion
        if is_path_in_ignored_folders(file_path, ignore_folders):
            continue

        # Process only .py files
        if not file_path.endswith(".py"):
            continue

        # Read content
        content = read_text(source, file_path)
        if content is None:
            continue

        # Extract imports
        imports = extract_imports_from_code(content, own_modules)
        all_imports.update(imports)

    # Convert to a standardized list of dictionaries
    result: list[Dependency] = []
    for import_name in sorted(all_imports):
        result.append(
            {
                "package": import_name,
                "used_version": "N/A",
                "pypi_version": "N/A",
                "status": STATUS_UNKNOWN,
            }
        )

    return result


def parse_imports_with_filter(
    source: ProjectSource, ignore_folders: list[str]
) -> list[Dependency]:
    """
    Wrapper for parse_imports with input validation.

    Args:
        source: Target Project source (ZipFile, TarFile, Path or dict).
        ignore_folders: Folders in Exclusion

    Returns:
        Standardized list of imports
    """
    return parse_imports(source, ignore_folders or [])
