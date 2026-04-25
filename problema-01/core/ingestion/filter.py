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

import zipfile
import tarfile
from typing import List, Tuple


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


def validate_archive_structure(
    archive, ignore_folders: List[str] = None
) -> Tuple[bool, str]:
    """
    Valida se o arquivo ZIP/TAR contém os requisitos mínimos para análise.

    Verifica se existem:
    1. Pelo menos um arquivo .py (fora de pastas ignoradas)
    2. Pelo menos um arquivo de dependências (requirements.txt, pyproject.toml,
       environment.yml, ou *.lock)

    Args:
        archive: Objeto zipfile.ZipFile ou tarfile.TarFile do projeto
        ignore_folders: Lista de pastas a ignorar (ex: ["tests", "docs"])

    Returns:
        Tupla (é_válido: bool, mensagem_erro: str)
        - (True, "") se válido
        - (False, "mensagem descritiva") se inválido
    """
    if archive is None:
        return False, "Arquivo não foi processado corretamente."

    if ignore_folders is None:
        ignore_folders = []

    DEPENDENCY_EXTENSIONS = (
        "requirements.txt",
        ".lock",
        "pyproject.toml",
        "environment.yml",
    )

    has_python_files = False
    has_dependency_file = False

    try:
        if isinstance(archive, zipfile.ZipFile):
            file_list = archive.filelist
        elif isinstance(archive, tarfile.TarFile):
            file_list = archive.getmembers()
        else:
            return False, "Tipo de arquivo não suportado."

        for member in file_list:
            file_path = getattr(member, "filename", None) or getattr(
                member, "name", None
            )
            if not file_path:
                continue

            if file_path.endswith("/"):
                continue

            if is_path_in_ignored_folders(file_path, ignore_folders):
                continue

            file_lower = file_path.lower()

            if file_lower.endswith(".py"):
                has_python_files = True

            if file_lower.endswith(DEPENDENCY_EXTENSIONS):
                has_dependency_file = True

            if has_python_files and has_dependency_file:
                return True, ""

    except Exception as e:
        return False, f"Erro ao validar arquivo: {str(e)}"

    if not has_python_files and not has_dependency_file:
        return (
            False,
            "❌ O ZIP deve conter:\n"
            "  1. Pelo menos um arquivo .py\n"
            "  2. Arquivo de dependências (requirements.txt, pyproject.toml, environment.yml ou .lock)",
        )
    elif not has_python_files:
        return (
            False,
            "❌ Nenhum arquivo .py encontrado no ZIP.\n"
            "Certifique-se de incluir código-fonte do seu projeto.",
        )
    else:  
        return (
            False,
            "❌ Nenhum arquivo de dependências encontrado.\n"
            "Incluir um dos seguintes: requirements.txt, pyproject.toml, environment.yml ou .lock",
        )
