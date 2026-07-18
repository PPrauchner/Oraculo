"""
Resolução de nomes entre Declaração e código para os analisadores.

Responsabilidades:
- Normalizar Nome de Distribuição e Nome de Import para uma forma comparável.
- Expandir uma Distribuição para todos os Nomes de Import que ela satisfaz,
  aplicando a tabela de Alias de Import (ex.: PyYAML -> yaml).
"""

from utils.constants import IMPORT_ALIASES


def normalize_name(name: str) -> str:
    """Normaliza um nome de pacote/import para comparação.

    Aplica minúsculas e troca "-" por "_", de modo que `scikit-learn` e
    `scikit_learn` casem.

    Args:
        name: Nome de Distribuição ou Nome de Import.

    Returns:
        O nome normalizado.
    """
    return name.lower().replace("-", "_")


def import_names_for(distribution: str) -> set[str]:
    """Retorna os Nomes de Import normalizados que uma Distribuição satisfaz.

    Além do próprio nome normalizado, inclui os Aliases de Import conhecidos
    (ex.: `PyYAML` também satisfaz `yaml`).

    Args:
        distribution: Nome de Distribuição declarado (ex.: "PyYAML").

    Returns:
        Conjunto de Nomes de Import normalizados equivalentes à Distribuição.
    """
    normalized = normalize_name(distribution)
    names = {normalized}
    names.update(normalize_name(alias) for alias in IMPORT_ALIASES.get(normalized, ()))
    return names
