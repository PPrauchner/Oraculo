"""
Identifies Ghost dependencies.

Ghost dependencies are those that are used in the code (imports),
but are not declared in the project's dependency files.

Input:
- Set of declared dependencies
- Set of imports used in the code

Output:
- Set of Ghost dependencies
"""

from core.analysis.name_matching import import_names_for, normalize_name
from utils.constants import ORIGIN_UNAVAILABLE
from utils.types import Dependency


def is_ghost(dep: Dependency) -> bool:
    """Indicates whether a dependency is a Ghost, by the absence of Origin.

    A Ghost does not come from a Declaration, so it has no Origin (CONTEXT.md) — that is
    the signal. It accepts both the missing key (the analyzers' output) and the "N/A"
    that the display and export layers fill in, so that the answer is
    the same on both sides of the pipeline.

    Args:
        dep: Dependency at any stage of the pipeline.

    Returns:
        True if the dependency is a Ghost.
    """
    return dep.get("origin", ORIGIN_UNAVAILABLE) == ORIGIN_UNAVAILABLE


def analyze_ghost_dependencies(
    declared: list[Dependency], imports: list[Dependency]
) -> list[Dependency]:
    """Identifies Ghost dependencies by comparing imports with declared dependencies."""
    declared_names: set[str] = set()
    for dep in declared:
        declared_names |= import_names_for(dep["package"])
    ghosts = []
    for imp in imports:
        if normalize_name(imp["package"]) not in declared_names:
            ghosts.append(imp)

    return ghosts
