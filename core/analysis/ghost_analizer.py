"""
Módulo responsável por identificar dependências fantasmas.

Dependências fantasmas são aquelas que são utilizadas no código (imports),
mas não estão declaradas nos arquivos de dependências do projeto.

Entrada:
- Conjunto de dependências declaradas
- Conjunto de imports utilizados no código

Saída:
- Conjunto de dependências fantasmas
"""

from core.analysis.name_matching import import_names_for, normalize_name


def analyze_ghost_dependencies(declared: list[dict], imports: list[dict]) -> list[dict]:
    """Identifica dependências fantasmas comparando imports com dependências declaradas."""
    declared_names: set[str] = set()
    for dep in declared:
        declared_names |= import_names_for(dep["Pacote"])
    ghosts = []
    for imp in imports:
        if normalize_name(imp["Pacote"]) not in declared_names:
            ghosts.append(imp)

    return ghosts
