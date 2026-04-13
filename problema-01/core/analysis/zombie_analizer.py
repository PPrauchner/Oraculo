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


def analyze_zombie_dependencies(
    declared: list[dict], imports: list[dict]
) -> list[dict]:
    """Identifica dependências zumbis comparando dependências declaradas com imports."""
    imp_names = {d["Pacote"].lower().replace("-", "_") for d in imports}
    zombies = []
    for imp in declared:
        declared_name = imp["Pacote"].lower().replace("-", "_")
        if declared_name not in imp_names:
            zombies.append(imp)

    return zombies
