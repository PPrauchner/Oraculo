"""
Módulo responsável por extrair imports do código-fonte.

Analisa arquivos Python utilizando AST (Abstract Syntax Tree)
para identificar dependências realmente utilizadas no código.

Entrada:
- Archive (ZIP/TAR) do projeto
- Pastas a ignorar

Saída:
- Lista de dicionários com imports encontrados:
  {
    "Pacote": "nome_do_modulo",
    "Versão Atual": "N/A",
    "Versão Pypi": "N/A",
    "Status": "Desconhecido"
  }
"""

import ast
import zipfile
import tarfile
from typing import Dict, List, Set, Optional
from core.ingestion.decompressor import get_archive_files
from core.ingestion.filter import is_path_in_ignored_folders
from utils.constants import PYTHON_STDLIB_MODULES


def is_valid_import(module_name: str) -> bool:
    """
    Verifica se um import é válido para análise de dependências.

    Rejeita:
    - Imports que começam com underscore (ex: _pytest, _internal)
    - Módulos nativos do Python (stdlib)

    Args:
        module_name: Nome do módulo importado (em lowercase)

    Returns:
        True se o import é válido, False caso contrário
    """
    # Rejeitar imports que começam com underscore
    if module_name.startswith("_"):
        return False

    # Rejeitar módulos nativos do Python
    if module_name in PYTHON_STDLIB_MODULES:
        return False

    return True


def extract_imports_from_code(code: str) -> Set[str]:
    """
    Extrai nomes de módulos importados de um código Python.

    Analisa o código usando AST e extrai:
    - import xxx
    - from xxx import yyy
    - from xxx.yyy import zzz

    Normaliza para o nome do pacote raíz (ex: "django.core" → "django")
    Filtra imports inválidos (comecoam com _, módulos stdlib)

    Args:
        code: Código Python em formato string

    Returns:
        Conjunto de nomes de módulos únicos
    """
    imports = set()

    try:
        # Extrair imports válidos antes do primeiro erro
        lines = code.split("\n")
        for line in lines:
            try:
                tree = ast.parse(line)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name
                            root_module = module_name.split(".")[0].lower()
                            if is_valid_import(root_module):
                                imports.add(root_module)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.level == 0:  # Ignorar relative imports
                            root_module = node.module.split(".")[0].lower()
                            if is_valid_import(root_module):
                                imports.add(root_module)
            except SyntaxError:
                # Continuar com próxima linha
                continue
    except Exception:
        # Fallback: tentar parse do arquivo todo
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        root_module = module_name.split(".")[0].lower()
                        if is_valid_import(root_module):
                            imports.add(root_module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.level == 0:
                        root_module = node.module.split(".")[0].lower()
                        if is_valid_import(root_module):
                            imports.add(root_module)
        except SyntaxError:
            pass

    return imports


def get_file_path_from_archive_member(member) -> str:
    """
    Extrai o caminho do arquivo de um membro ZipInfo ou TarInfo.

    Args:
        member: ZipInfo ou TarInfo object

    Returns:
        String do caminho do arquivo
    """
    if isinstance(member, zipfile.ZipInfo):
        return member.filename
    elif isinstance(member, tarfile.TarInfo):
        return member.name
    return ""


def read_file_from_archive(archive, member) -> Optional[str]:
    """
    Lê o conteúdo de um arquivo do archive.

    Args:
        archive: ZipFile ou TarFile object
        member: ZipInfo ou TarInfo object

    Returns:
        Conteúdo do arquivo como string, ou None se falhar
    """
    try:
        if isinstance(archive, zipfile.ZipFile):
            content = archive.read(member.filename)
        elif isinstance(archive, tarfile.TarFile):
            f = archive.extractfile(member)
            if f is None:
                return None
            content = f.read()
        else:
            return None

        return content.decode("utf-8", errors="ignore")
    except Exception:
        return None


def parse_imports(archive, ignore_folders: List[str]) -> List[Dict[str, str]]:
    """
    Extrai imports de todos os arquivos Python do archive.

    Itera pelos arquivos Python, respeita pastas ignoradas,
    extrai imports e retorna lista padronizada.

    Args:
        archive: ZipFile ou TarFile do projeto
        ignore_folders: Lista de pastas a ignorar (ex: ["tests", "docs"])

    Returns:
        Lista de dicionários com imports encontrados
    """
    if not archive:
        return []

    all_imports = set()
    file_list = get_archive_files(archive)

    for member in file_list:
        file_path = get_file_path_from_archive_member(member)

        # Verificar se arquivo deve ser ignorado
        if is_path_in_ignored_folders(file_path, ignore_folders):
            continue

        # Processar apenas arquivos .py
        if not file_path.endswith(".py"):
            continue

        # Ler conteúdo
        content = read_file_from_archive(archive, member)
        if content is None:
            continue

        # Extrair imports
        imports = extract_imports_from_code(content)
        all_imports.update(imports)

    # Converter para lista de dicionários padronizada
    result = []
    for import_name in sorted(all_imports):
        result.append(
            {
                "Pacote": import_name,
                "Versão Atual": "N/A",
                "Versão PyPI": "N/A",
                "Status": "Desconhecido",
            }
        )

    return result


def parse_imports_with_filter(
    archive, ignore_folders: List[str]
) -> List[Dict[str, str]]:
    """
    Wrapper para parse_imports com validação de entrada.

    Args:
        archive: ZipFile ou TarFile do projeto
        ignore_folders: Lista de pastas a ignorar

    Returns:
        Lista de imports padronizada
    """
    return parse_imports(archive, ignore_folders or [])
