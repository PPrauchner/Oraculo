"""
Aplica as Exclusões e confere os requisitos mínimos do Projeto-Alvo.

Responsabilidades:
- Oferecer as pastas do Projeto-Alvo que podem virar Exclusão.
- Decidir se um caminho está dentro de uma Exclusão.
- Validar que o Projeto-Alvo tem código Python e ao menos uma Declaração.

Trabalha sobre caminhos vindos de `core.ingestion.source`, e por isso vale igual
para archive e para diretório (ADR-0001). Uma Exclusão é o **nome de uma pasta**, e
casa em qualquer profundidade: marcar `tests` exclui `tests/` e `src/tests/`.
"""

from core.ingestion.source import ProjectSource, is_supported, list_paths


def _folder_name(folder: str) -> str:
    """Reduz uma Exclusão ao nome da pasta, tolerando `./tests/` e `.\\tests`."""
    return folder.replace("\\", "/").strip("/").removeprefix("./").strip()


def get_unique_folders(source: ProjectSource) -> list[str]:
    """Lista as pastas do Projeto-Alvo que podem virar Exclusão.

    Toda pasta devolvida aqui é excluível por `is_path_in_ignored_folders`: as duas
    funções falam da mesma coisa — nome de pasta em qualquer profundidade. Foi a
    divergência entre elas que fazia a UI oferecer Exclusões sem efeito (issue #26).

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).

    Returns:
        Nomes de pasta, sem repetição, em ordem alfabética.
    """
    folders = set()

    for path in list_paths(source):
        # O último segmento é o arquivo, não uma pasta
        folders.update(path.split("/")[:-1])

    return sorted(folders)


def is_path_in_ignored_folders(file_path: str, ignore_folders: list[str]) -> bool:
    """Indica se um caminho está dentro de alguma Exclusão.

    Casa por segmento, em qualquer profundidade: marcar `tests` exclui tanto
    `tests/test_x.py` quanto `src/tests/test_x.py`. Um arquivo cujo nome coincide
    com a Exclusão não é excluído — Exclusão é pasta.

    Args:
        file_path: Caminho do arquivo, relativo à raiz do Projeto-Alvo.
        ignore_folders: Pastas em Exclusão (ex.: ["tests", "docs"]).

    Returns:
        True se o arquivo está em uma Exclusão, False caso contrário.
    """
    if not ignore_folders or not file_path:
        return False

    parent_segments = set(file_path.replace("\\", "/").strip("/").split("/")[:-1])
    excluded_names = {_folder_name(folder) for folder in ignore_folders}

    return not excluded_names.isdisjoint(parent_segments)


def should_skip_file(file_path: str, ignore_folders: list[str]) -> bool:
    """
    Verifica se um arquivo deve ser ignorado.

    Args:
        file_path: Caminho do arquivo
        ignore_folders: Lista de pastas a ignorar

    Returns:
        True se arquivo deve ser ignorado, False caso contrário
    """
    return is_path_in_ignored_folders(file_path, ignore_folders)


def validate_project_structure(
    source: ProjectSource, ignore_folders: list[str] | None = None
) -> tuple[bool, str]:
    """Valida se o Projeto-Alvo tem os requisitos mínimos para a auditoria.

    Exige, fora das Exclusões, pelo menos um arquivo `.py` e pelo menos uma
    Declaração (ou Lock). Vale igual para archive e para diretório, então as
    mensagens não citam formato de arquivo.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).
        ignore_folders: Pastas em Exclusão (ex.: ["tests", "docs"]).

    Returns:
        Par (é_válido, mensagem_de_erro). Com sucesso, (True, "").
    """
    if source is None:
        return False, "❌ O Projeto-Alvo não foi processado corretamente."

    # Fonte que o despacho não abre produz lista de caminhos vazia, indistinguível
    # de um Projeto-Alvo sem código. Sem esta saída, o usuário ouviria que faltam
    # arquivos .py num Projeto-Alvo que sequer chegou a ser lido.
    if not is_supported(source):
        return False, (
            "❌ Fonte do Projeto-Alvo não suportada.\n"
            "Informe um diretório local ou um archive (zip, tar.gz ou tar)."
        )

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
        for file_path in list_paths(source):
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
        return False, f"❌ Erro ao ler o Projeto-Alvo: {str(e)}"

    if not has_python_files and not has_dependency_file:
        return (
            False,
            "❌ O Projeto-Alvo deve conter:\n"
            "  1. Pelo menos um arquivo .py\n"
            "  2. Arquivo de dependências (requirements.txt, pyproject.toml, environment.yml ou .lock)",
        )
    elif not has_python_files:
        return (
            False,
            "❌ Nenhum arquivo .py encontrado no Projeto-Alvo.\n"
            "Certifique-se de que o código-fonte está incluído e fora das Exclusões.",
        )
    else:
        return (
            False,
            "❌ Nenhum arquivo de dependências encontrado.\n"
            "Incluir um dos seguintes: requirements.txt, pyproject.toml, environment.yml ou .lock",
        )
