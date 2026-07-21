"""
Identifies Zombie dependencies.

Zombie dependencies are those that are declared in the project,
but are not used in the code (they do not appear in the imports).

Input:
- Set of declared dependencies
- Set of imports used in the code

Output:
- Set of Zombie dependencies
"""

from core.analysis.name_matching import import_names_for, normalize_name
from utils.constants import ORIGIN_DEVELOPMENT
from utils.types import Dependency


def analyze_zombie_dependencies(
    declared: list[Dependency], imports: list[Dependency]
) -> list[Dependency]:
    """Identifies Zombie dependencies by comparing declared dependencies with imports.

    A Development Dependency is never a Zombie (ADR-0003): its Origin is a
    development group, so it is exempt even when no Root Import
    corresponds to it. It stays in the Total and receives Size, Age and Outdated
    status — it is simply not held to account for not being imported.
    """
    imp_names = {normalize_name(d["package"]) for d in imports}
    zombies = []
    for dep in declared:
        if dep.get("origin") == ORIGIN_DEVELOPMENT:
            continue
        if imp_names.isdisjoint(import_names_for(dep["package"])):
            zombies.append(dep)

    return zombies
