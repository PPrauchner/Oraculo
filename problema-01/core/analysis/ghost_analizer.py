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

# ============================================================= #
#                         Dados  Mock                           #
list_ghosts = [
    {
        "name": "ghost-package-1",
        "current_version": "2.0.0",
        "pypi_version": "2.0.0",
        "status": "Atualizado",
    },
    {
        "name": "ghost-package-2",
        "current_version": "2.5.0",
        "pypi_version": "2.5.0",
        "status": "Atualizado",
    },
]
