"""
Módulo responsável pela filtragem de arquivos e diretórios.

Aplica regras definidas pelo usuário para ignorar arquivos ou diretórios
irrelevantes para a análise (ex: tests/, docs/).

Entrada:
- Lista de arquivos do projeto
- Regras de exclusão

Saída:
- Lista filtrada de arquivos relevantes para análise
"""
import os
from pathlib import Path
from core.constants import _DEFAULT_IGNORED_DIRS, _DEFAULT_IGNORED_SUFFIXES, _CONFIG_FILES

def filter_python_files(root_dir, exclusions=None):
    """Retorna uma lista com os caminhos de todos os arquivos
    relevantes encontrados dentro da pasta do projeto.

    Args:
        root_dir (str): Caminho da pasta extraída pelo decompressor.
        exclusions (list): Pastas a ignorar definidas pelo usuário.
                           Exemplo: ["tests", "docs"]

    Returns:
        list[str]: Lista com os caminhos completos dos arquivos válidos.
    """

    root = Path(root_dir).resolve()

    if not root.exists() or not root.is_dir():
        raise ValueError(f"Diretório inválido ou não encontrado: {root}")

    if exclusions is None:
        exclusions = []

    user_exclusions = [e.strip().lower() for e in exclusions]
    files = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not _should_ignore_dir(d, user_exclusions)]

        for name in filenames:
            name_without_ext = Path(name).stem.lower()

            if name.lower() in user_exclusions or name_without_ext in user_exclusions:
                continue

            is_python = name.endswith(".py")
            is_config = name.lower() in _CONFIG_FILES

            if not (is_python or is_config):
                continue

            files.append(str(Path(dirpath) / name))

    return sorted(files)


def _should_ignore_dir(dir_name, user_exclusions):
    """Verifica se uma pasta deve ser ignorada.

    Retorna True se a pasta deve ser ignorada, False caso contrário.

    Args:
        dir_name (str): Nome da pasta sendo verificada.
        user_exclusions (list): Exclusões definidas pelo usuário em lowercase.
    """
    name_lower = dir_name.lower()

    if name_lower in _DEFAULT_IGNORED_DIRS or name_lower in user_exclusions:
        return True

    for suffix in _DEFAULT_IGNORED_SUFFIXES:
        if name_lower.endswith(suffix):
            return True

    return False