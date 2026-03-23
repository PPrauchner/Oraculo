"""
core/ingestion/filter.py

Responsabilidade:
    Recebe a pasta extraída pelo decompressor e entrega apenas os arquivos
    .py relevantes para o parsing.

    É chamado entre o decompressor e o parsing:
        decompressor.py  →  filter.py  →  parsing/

Função exportada:
    filter_python_files(root_dir, exclusions)
"""

import os
import sys
from pathlib import Path


# Lista de pastas que sempre devem ser ignoradas
# independente do que o usuário configurar
_DEFAULT_IGNORED_DIRS = [
    ".venv", "venv", ".env", "env",
    "__pycache__", ".git", ".mypy_cache",
    ".pytest_cache", ".ruff_cache",
    "node_modules", "dist", "build",
    ".eggs",
]

# Pastas que terminam com esse sufixo também são ignoradas
_DEFAULT_IGNORED_SUFFIXES = [".egg-info"]


def filter_python_files(root_dir, exclusions=None):
    """Retorna uma lista com os caminhos de todos os arquivos .py
    relevantes encontrados dentro da pasta do projeto.

    Args:
        root_dir (str): Caminho da pasta extraída pelo decompressor.
        exclusions (list): Pastas a ignorar definidas pelo usuário.
                           Exemplo: ["tests", "docs"]

    Returns:
        list[str]: Lista com os caminhos completos dos arquivos .py válidos.
    """

    # Transforma o caminho em um objeto Path e resolve o caminho absoluto
    root = Path(root_dir).resolve()

    # Verifica se a pasta existe antes de tentar percorrê-la
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Diretório inválido ou não encontrado: {root}")

    # Se o usuário não passou nenhuma exclusão, usa uma lista vazia
    if exclusions is None:
        exclusions = []

    # Converte as exclusões para lowercase para comparação sem erros de capitalização
    user_exclusions = [e.strip().lower() for e in exclusions]

    # Lista que vai acumulando os caminhos dos arquivos válidos
    files = []

    # os.walk percorre a pasta e todas as subpastas automaticamente
    # dirpath   = caminho da pasta atual
    # dirnames  = lista de subpastas dentro da pasta atual
    # filenames = lista de arquivos dentro da pasta atual
    for dirpath, dirnames, filenames in os.walk(root):

        # Remove da lista as pastas que devem ser ignoradas
        # Isso faz o os.walk não entrar nessas pastas
        dirnames[:] = [
            d for d in dirnames
            if not _should_ignore_dir(d, user_exclusions)
        ]

        # Verifica cada arquivo da pasta atual
        for name in filenames:

            # Ignora arquivos que não são .py
            if not name.endswith(".py"):
                continue

            # Ignora arquivos cujo nome está na lista de exclusões do usuário
            if name.lower() in user_exclusions:
                continue

            # Monta o caminho completo do arquivo e adiciona na lista
            files.append(str(Path(dirpath) / name))

    # Retorna a lista ordenada alfabeticamente
    return sorted(files)


def _should_ignore_dir(dir_name, user_exclusions):
    """Verifica se uma pasta deve ser ignorada.

    Retorna True se a pasta deve ser ignorada, False caso contrário.

    Args:
        dir_name (str): Nome da pasta sendo verificada.
        user_exclusions (list): Exclusões definidas pelo usuário em lowercase.
    """

    # Converte para lowercase para comparação sem erros de capitalização
    name_lower = dir_name.lower()

    # Verifica se está na lista de pastas ignoradas automaticamente
    if name_lower in _DEFAULT_IGNORED_DIRS:
        return True

    # Verifica se está na lista de exclusões do usuário
    if name_lower in user_exclusions:
        return True

    # Verifica se termina com algum sufixo ignorado (ex: .egg-info)
    for suffix in _DEFAULT_IGNORED_SUFFIXES:
        if name_lower.endswith(suffix):
            return True

    # Se não caiu em nenhuma verificação acima, a pasta é válida
    return False


# Esse bloco só executa quando o arquivo é rodado diretamente
# Quando outro módulo importa o filter.py, esse bloco é ignorado
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Uso: python filter.py <caminho_do_projeto> [exclusao1 exclusao2 ...]")
        print("Exemplo: python filter.py /tmp/meu_projeto tests docs")
        sys.exit(1)

    directory      = sys.argv[1]
    cli_exclusions = sys.argv[2:]

    print(f"\nDiretório  : {directory}")
    print(f"Exclusões  : {cli_exclusions or 'nenhuma'}")
    print("-" * 50)

    try:
        files = filter_python_files(directory, cli_exclusions)
    except ValueError as e:
        print(f"Erro: {e}")
        sys.exit(1)

    print(f"Arquivos .py encontrados: {len(files)}")
    for f in files:
        print(f"  {f}")