"""
Reading and parsing of dependency configuration files.

Loads and extracts raw data from files such as:
- requirements.txt (pip standard)
- pyproject.toml  (PEP 621 and Poetry)
- environment.yml (Conda)
- *.lock          (uv.lock, poetry.lock — TOML format)

Input:
- Configuration file content (string)

Output:
- List of dictionaries containing 'Package', 'Used Version' and 'Origin'
"""

import re
import tomllib
from typing import Dict, List, Optional

import yaml

from utils.constants import ORIGIN_DEVELOPMENT, ORIGIN_PRODUCTION
from utils.types import DeclarationEntry
from utils.functions import READERS, registrar


def parse_dependency_string(line: str) -> Optional[DeclarationEntry]:
    """
    Parses a line of text and returns the dependency's name and Used Version.

    Only an exact pin determines the Used Version; a range specifier fixes
    no version at all and returns "" (ADR-0002). Without this, `!=1.25.0,>=1.21.1` would
    fall into the trap of reporting the *excluded* version as used.

    Handles the following PEP 508 cases and common formats:
    - Exact pin:                 requests==2.31.0                  → requests | 2.31.0
    - Environment markers: numpy>=1.26; python_version < '3.14'     → numpy | ""
    - Extras in brackets: requests[security]>=2.28                  → requests | ""
    - Multiple specifiers:       urllib3!=1.25.0,>=1.21.1          → urllib3 | ""
    - Name only, no version:     Pillow                            → pillow | ""
    - Conditional dependency, no version: tzdata; sys_platform==... → tzdata | ""

    Args:
        line: Line of text with the dependency declaration.

    Returns:
        Dict with 'Package' and 'Used Version', or None if the line is invalid.
    """
    line = line.split("#")[0].strip()
    if not line:
        return None

    line = line.split(";")[0].strip()

    line = re.sub(r"\[.*?\]", "", line).strip()

    if not line:
        return None

    match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", line)
    if not match:
        return None

    name = match.group(1).strip().lower()
    version_raw = match.group(2).strip()

    # Only an exact pin (== from PEP 508, === from PEP 440) fixes the Used Version; a
    # range specifier (>=, <, !=, ^, ~=) does not determine a version (ADR-0002).
    pin_match = re.match(r"={2,3}\s*(\d[^\s,;]*)", version_raw)
    version = pin_match.group(1) if pin_match else ""

    return {"package": name, "used_version": version}


def _clean_conda_dep(dep_string: str) -> Optional[DeclarationEntry]:
    """
    Parses a Conda dependency entry (environment.yml).

    Conda uses formats such as: 'numpy', 'numpy=1.24', 'numpy>=1.24'.
    Ignores entries with ':' (specific channel like 'conda-forge::numpy').

    Args:
        dep_string: Conda dependency string.

    Returns:
        Dict with 'Package' and 'Used Version', or None if invalid.
    """
    dep_string = str(dep_string).strip()

    if "::" in dep_string:
        dep_string = dep_string.split("::")[-1]

    dep_string = re.sub(r"(?<![=<>!])=(?!=)", "==", dep_string)

    return parse_dependency_string(dep_string)


def _parse_dependency_list(entries: List[str], origin: str) -> List[DeclarationEntry]:
    """
    Parses a list of PEP 508 declarations and stamps the Origin of each one.

    Ignores 'python', which is the interpreter and not a PyPI package.

    Args:
        entries: Declaration lines (e.g.: ["requests>=2.33.0"]).
        origin: Origin to assign to each package in the list.

    Returns:
        List of dicts with 'Package', 'Used Version' and 'Origin'.
    """
    if not isinstance(entries, list):
        return []

    dependencies: List[DeclarationEntry] = []
    for entry in entries:
        result = parse_dependency_string(str(entry))
        if result and result["package"] != "python":
            result["origin"] = origin
            dependencies.append(result)
    return dependencies


def _as_dict(value: object) -> Dict[str, object]:
    """Returns value if it is a table; otherwise, an empty table.

    A pyproject.toml of an arbitrary Target Project may be malformed (e.g.:
    [tool.poetry.group] declared as a string). Normalizing each section to a
    dict before sweeping avoids AttributeError and degrades cleanly.

    Args:
        value: Value read from the TOML, of unknown type.

    Returns:
        The value itself when it is a dict; otherwise, an empty dict.
    """
    return value if isinstance(value, dict) else {}


def _as_pep_508_specifier(spec: object) -> str:
    """Converts a Poetry specifier to the form PEP 508 writes.

    Poetry accepts an exact pin with no operator (`requests = "2.33.0"`), which in PEP 508
    is written `requests==2.33.0`. Without the conversion the number sticks to the name
    ("requests2.33.0") and the pin is lost — and it is the only source of Used Version
    outside the Lock (ADR-0002). Ranges (`^`, `~`, `>=`) and the `*` wildcard pass
    through intact: they do not fix a version.

    Args:
        spec: Specifier read from the TOML.

    Returns:
        The specifier ready to concatenate to the Distribution Name.
    """
    text = str(spec).strip()

    if text[:1].isdigit():
        return f"=={text}"

    return text


def _parse_dependency_table(table: Dict[str, object], origin: str) -> List[DeclarationEntry]:
    """
    Parses a Poetry dependency table and stamps the Origin of each one.

    Poetry declares dependencies as name/specifier pairs, where the
    specifier can be a string ("^2.33.0") or a table with the version
    and extra options ({version = "^2.33.0", extras = ["security"]}).

    Args:
        table: Table of name → version specifier.
        origin: Origin to assign to each package in the table.

    Returns:
        List of dicts with 'Package', 'Used Version' and 'Origin'.
    """
    if not isinstance(table, dict):
        return []

    entries = []
    for name, spec in table.items():
        if isinstance(spec, dict):
            spec = spec.get("version", "")
        entries.append(f"{name}{_as_pep_508_specifier(spec)}")
    return _parse_dependency_list(entries, origin)


def _parse_requirements_content(content: str, origin: str) -> List[DeclarationEntry]:
    """
    Reads the content of a requirements file and stamps the Origin of each dependency.

    Supports lines with and without a version, ignores comments and pip
    option lines (e.g.: -r, --index-url).

    Args:
        content: Full file content as a string.
        origin: Origin to assign to each declared package.

    Returns:
        List of dicts with 'Package', 'Used Version' and 'Origin'.
    """
    lines = [line.strip() for line in content.split("\n")]
    return _parse_dependency_list(
        [line for line in lines if not line.startswith("-")], origin
    )


@registrar(READERS, "requirements.txt")
def parse_requirements(content: str) -> List[DeclarationEntry]:
    """
    Reads a requirements.txt, whose dependencies are Production.

    Args:
        content: Full file content as a string.

    Returns:
        List of dicts with 'Package', 'Used Version' and 'Origin'.
    """
    return _parse_requirements_content(content, ORIGIN_PRODUCTION)


@registrar(READERS, "requirements-dev.txt")
def parse_requirements_dev(content: str) -> List[DeclarationEntry]:
    """
    Reads a requirements-dev.txt, whose dependencies are Development.

    Needs its own registration: 'requirements-dev.txt' does not end in
    'requirements.txt', so it would never match the Production reader.

    Args:
        content: Full file content as a string.

    Returns:
        List of dicts with 'Package', 'Used Version' and 'Origin'.
    """
    return _parse_requirements_content(content, ORIGIN_DEVELOPMENT)


@registrar(READERS, "environment.yml")
def parse_environment_yml(content: str) -> List[DeclarationEntry]:
    """
    Reads an environment.yml (Conda) and extracts its dependencies.

    Supports two kinds of entry in the 'dependencies' list:
    - Plain string: "numpy=1.24.0" or "numpy>=1.24"
    - Dict with 'pip': list of pip packages inside the conda environment

    Ignores entries that are not Python packages (e.g.: "python=3.11").

    The environment.yml describes the Target Project's runtime environment, so
    its packages are Production Dependencies.

    Args:
        content: Full file content as a string.

    Returns:
        List of dicts with 'Package', 'Used Version' and 'Origin'.
    """
    dependencies: List[DeclarationEntry] = []

    try:
        data = yaml.safe_load(content)
    except Exception:
        return []

    if not isinstance(data, dict):
        return []

    for entry in data.get("dependencies") or []:

        if isinstance(entry, str):
            if entry.strip().lower().startswith("python"):
                continue
            result = _clean_conda_dep(entry)
            if result:
                result["origin"] = ORIGIN_PRODUCTION
                dependencies.append(result)
            continue

        if isinstance(entry, dict) and "pip" in entry:
            dependencies += _parse_dependency_list(
                entry.get("pip", []), ORIGIN_PRODUCTION
            )

    return dependencies


@registrar(READERS, "pyproject.toml")
def parse_pyproject(content: str) -> List[DeclarationEntry]:
    """
    Reads a pyproject.toml (PEP 621 and Poetry) and extracts its dependencies.

    Preserves the Origin of each package:
    - [project].dependencies and [tool.poetry].dependencies → Production
    - [dependency-groups] and [project.optional-dependencies] → Development
    - [tool.poetry.group.<name>.dependencies] → Development, whatever
      the group name is

    Args:
        content: Full file content as a string.

    Returns:
        List of dicts with 'Package', 'Used Version' and 'Origin'.
    """
    try:
        data = tomllib.loads(content)
    except Exception:
        return []

    if not isinstance(data, dict):
        return []

    project = _as_dict(data.get("project"))

    dependencies = _parse_dependency_list(
        project.get("dependencies", []), ORIGIN_PRODUCTION
    )

    for extra in _as_dict(project.get("optional-dependencies")).values():
        dependencies += _parse_dependency_list(extra, ORIGIN_DEVELOPMENT)

    for group in _as_dict(data.get("dependency-groups")).values():
        dependencies += _parse_dependency_list(group, ORIGIN_DEVELOPMENT)

    poetry = _as_dict(_as_dict(data.get("tool")).get("poetry"))
    dependencies += _parse_dependency_table(
        poetry.get("dependencies", {}), ORIGIN_PRODUCTION
    )

    for group in _as_dict(poetry.get("group")).values():
        dependencies += _parse_dependency_table(
            _as_dict(group).get("dependencies", {}), ORIGIN_DEVELOPMENT
        )

    return dependencies


@registrar(READERS, ".lock")
def parse_lock(content: str) -> List[DeclarationEntry]:
    """
    Reads *.lock files in TOML format (uv.lock, poetry.lock).

    Both managers store packages in a 'package' list
    with the fields 'name' and 'version'.

    The Lock resolves versions, it does not define the audited set (ADR-0002): it does not
    separate production from development, so its packages are set as Production.

    Args:
        content: Full file content as a string.

    Returns:
        List of dicts with 'Package', 'Used Version' and 'Origin'.
    """
    dependencies: List[DeclarationEntry] = []

    try:
        data = tomllib.loads(content)
    except Exception:
        return []

    for package in data.get("package", []):
        name = package.get("name")
        version = package.get("version", "")
        if name and name.lower() != "python":
            dependencies.append(
                {
                    "package": name.lower(),
                    "used_version": version if version else "",
                    "origin": ORIGIN_PRODUCTION,
                }
            )

    return dependencies
