"""
Módulo responsável por identificar dependências zumbis.

Dependências zumbis são aquelas que estão declaradas no projeto,
mas não são utilizadas no código (não aparecem nos imports).

Entrada:
- Conjunto de dependências declaradas
- Conjunto de imports utilizados no código

Saída:
- Conjunto de dependências zumbis
"""

from core.analysis.name_matching import import_names_for, normalize_name


def analyze_zombie_dependencies(
    declared: list[dict], imports: list[dict]
) -> list[dict]:
    """Identifica dependências zumbis comparando dependências declaradas com imports."""
    imp_names = {normalize_name(d["Pacote"]) for d in imports}
    zombies = []
    for dep in declared:
        if imp_names.isdisjoint(import_names_for(dep["Pacote"])):
            zombies.append(dep)

    return zombies
