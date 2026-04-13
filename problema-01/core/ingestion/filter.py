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

from typing import List


def get_unique_folders(extracted_files: list) -> list:
    if not extracted_files:
        return []

    folders = set()
    for file in extracted_files:
        path = getattr(file, "filename", None) or getattr(file, "name", None)
        if path:
            parts = path.split("/")
            for i in range(len(parts) - 1):
                folders.add(parts[i])

    return sorted(list(folders))


def is_path_in_ignored_folders(file_path: str, ignore_folders: List[str]) -> bool:
    """
    Verifica se um caminho de arquivo está dentro de uma pasta ignorada.

    Args:
        file_path: Caminho do arquivo (ex: "tests/requirements.txt")
        ignore_folders: Lista de pastas a ignorar (ex: ["tests", "docs"])

    Returns:
        True se o arquivo está em uma pasta ignorada, False caso contrário
    """
    if not ignore_folders:
        return False

    if not file_path:
        return False

    # Normalizar o caminho
    normalized_path = file_path.lstrip("./").replace("\\", "/")

    # Verificar se qualquer folder no caminho está na lista de ignorados
    for folder in ignore_folders:
        normalized_folder = folder.lstrip("./").replace("\\", "/")

        if (
            normalized_path.startswith(normalized_folder + "/")
            or normalized_path == normalized_folder
        ):
            return True

    return False


def should_skip_file(file_path: str, ignore_folders: List[str]) -> bool:
    """
    Verifica se um arquivo deve ser ignorado.

    Args:
        file_path: Caminho do arquivo
        ignore_folders: Lista de pastas a ignorar

    Returns:
        True se arquivo deve ser ignorado, False caso contrário
    """
    return is_path_in_ignored_folders(file_path, ignore_folders)
