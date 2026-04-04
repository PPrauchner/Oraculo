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

# ============================================================= #
#                         Dados  Mock                           #
list_zombies = [
    {
        "name": "zombie-package-1",
        "current_version": "2.0.0",
        "pypi_version": "2.0.0",
        "status": "Atualizado",
    },
    {
        "name": "zombie-package-2",
        "current_version": "2.5.0",
        "pypi_version": "2.5.0",
        "status": "Atualizado",
    },
]
