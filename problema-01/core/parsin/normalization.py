"""
Módulo responsável pela normalização de dependências.

Padroniza nomes de pacotes e versões para garantir comparações corretas
entre dependências declaradas e imports utilizados.

Exemplo:
- "Flask" → "flask"
- "flask==2.0.0" → "flask"

Entrada:
- Listas de dependências (ex: requirements.txt, imports)

Saída:
- Listas normalizadas de dependências para análise (ex: listad de dicionários)
"""

# ============================================================= #
#                         Dados  Mock                           #
list_all = [
    {
        "name": "package-1",
        "current_version": "2.0.0",
        "pypi_version": "2.0.0",
        "status": "Atualizado",
    },
    {
        "name": "package-2",
        "current_version": "2.5.0",
        "pypi_version": "2.5.0",
        "status": "Atualizado",
    },
    {
        "name": "package-3",
        "current_version": "2.2.0",
        "pypi_version": "2.2.0",
        "status": "Atualizado",
    },
    {
        "name": "package-4",
        "current_version": "2.2.0",
        "pypi_version": "2.2.0",
        "status": "Atualizado",
    },
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
    {
        "name": "outdated-package-1",
        "current_version": "1.0.0",
        "pypi_version": "2.0.0",
        "status": "Desatualizado",
    },
    {
        "name": "outdated-package-2",
        "current_version": "1.5.0",
        "pypi_version": "2.5.0",
        "status": "Desatualizado",
    },
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
