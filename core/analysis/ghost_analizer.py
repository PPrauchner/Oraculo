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


def analyze_ghost_dependencies(declared: list[dict], imports: list[dict]) -> list[dict]:
    """Identifica dependências fantasmas comparando imports com dependências declaradas."""
    declared_names = {d["Pacote"].lower().replace("-", "_") for d in declared}
    ghosts = []
    for imp in imports:
        imp_name = imp["Pacote"].lower().replace("-", "_")
        if imp_name not in declared_names:
            ghosts.append(imp)

    return ghosts
