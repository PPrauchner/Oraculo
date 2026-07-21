"""
Name resolution between Declaration and code for the analyzers.

Responsibilities:
- Normalize Distribution Name and Import Name into a comparable form.
- Expand a Distribution into all the Import Names it satisfies,
  applying the Import Alias table (e.g.: PyYAML -> yaml).
"""

from utils.constants import IMPORT_ALIASES


def normalize_name(name: str) -> str:
    """Normalizes a package/import name for comparison.

    Lowercases and swaps "-" for "_", so that `scikit-learn` and
    `scikit_learn` match.

    Args:
        name: Distribution Name or Import Name.

    Returns:
        The normalized name.
    """
    return name.lower().replace("-", "_")


def import_names_for(distribution: str) -> set[str]:
    """Returns the normalized Import Names that a Distribution satisfies.

    Beyond its own normalized name, it includes the known Import Aliases
    (e.g.: `PyYAML` also satisfies `yaml`).

    Args:
        distribution: Declared Distribution Name (e.g.: "PyYAML").

    Returns:
        Set of normalized Import Names equivalent to the Distribution.
    """
    normalized = normalize_name(distribution)
    names = {normalized}
    names.update(normalize_name(alias) for alias in IMPORT_ALIASES.get(normalized, ()))
    return names
