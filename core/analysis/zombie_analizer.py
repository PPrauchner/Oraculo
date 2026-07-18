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
from utils.constants import ORIGIN_DEVELOPMENT


def analyze_zombie_dependencies(
    declared: list[dict], imports: list[dict]
) -> list[dict]:
    """Identifica dependências zumbis comparando dependências declaradas com imports.

    Dependência de Desenvolvimento nunca é Zumbi (ADR-0003): sua Origem é um
    grupo de desenvolvimento, então é isenta mesmo quando nenhum Import Raiz
    corresponde a ela. Continua no Total e recebe Tamanho, Idade e status de
    Desatualizada — apenas não é cobrada por não ser importada.
    """
    imp_names = {normalize_name(d["Pacote"]) for d in imports}
    zombies = []
    for dep in declared:
        if dep.get("Origem") == ORIGIN_DEVELOPMENT:
            continue
        if imp_names.isdisjoint(import_names_for(dep["Pacote"])):
            zombies.append(dep)

    return zombies
