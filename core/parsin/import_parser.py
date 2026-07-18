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
    "Versão Usada": "N/A",
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

# Pasta que apenas embrulha os Módulos Próprios num layout `src/`
SRC_LAYOUT_FOLDER = "src"


def _normalize_paths(file_paths: List[str]) -> List[str]:
    """
    Uniformiza os caminhos vindos da ingestão (archive ou diretório).

    Args:
        file_paths: Caminhos crus, possivelmente com separador do Windows,
            prefixo "./" ou barra final (entradas de pasta do archive).

    Returns:
        Lista de caminhos com separador "/" e sem entradas vazias.
    """
    normalized = []

    for path in file_paths:
        clean = path.replace("\\", "/").rstrip("/")
        if clean.startswith("./"):
            clean = clean[2:]
        if clean:
            normalized.append(clean)

    return normalized


def _strip_project_root(file_paths: List[str]) -> List[str]:
    """
    Remove a pasta que apenas embrulha o Projeto-Alvo, se houver.

    Um archive normalmente contém tudo dentro de uma pasta raiz
    (`grupo-03/core/...`); nesse caso o topo do projeto é dentro dela. A pasta só
    é embrulho se não for, ela mesma, um pacote.

    Args:
        file_paths: Caminhos já normalizados.

    Returns:
        Caminhos relativos à raiz do Projeto-Alvo.
    """
    top_segments = {path.split("/")[0] for path in file_paths}
    if len(top_segments) != 1:
        return file_paths

    root = top_segments.pop()

    # Raiz que é um pacote (ou um arquivo solto) não é embrulho
    if root.endswith(".py") or f"{root}/__init__.py" in file_paths:
        return file_paths

    return [path[len(root) + 1 :] for path in file_paths if path != root]


def infer_own_modules(file_paths: List[str]) -> Set[str]:
    """
    Infere os Módulos Próprios a partir do layout do Projeto-Alvo.

    Um Módulo Próprio é um pacote definido pelo próprio Projeto-Alvo, reconhecível
    por existir como pasta de topo com `__init__.py`. A inferência usa apenas os
    caminhos já disponíveis na ingestão (archive ou diretório), sem I/O extra.

    Args:
        file_paths: Caminhos dos arquivos do Projeto-Alvo, relativos à sua raiz.

    Returns:
        Conjunto de nomes de Módulos Próprios, em lowercase.
    """
    own_modules = set()

    for path in file_paths:
        parts = path.split("/")

        # Num layout `src/`, os Módulos Próprios são as pastas dentro dele
        if parts[0] == SRC_LAYOUT_FOLDER:
            parts = parts[1:]

        # Pasta de topo com __init__.py: pacote do Projeto-Alvo
        if len(parts) >= 2 and parts[1] == "__init__.py":
            own_modules.add(parts[0].lower())

        # Arquivo .py de topo: módulo do Projeto-Alvo
        elif len(parts) == 1 and parts[0].endswith(".py"):
            own_modules.add(parts[0][: -len(".py")].lower())

    return own_modules


def is_valid_import(module_name: str, own_modules: Set[str] | None = None) -> bool:
    """
    Verifica se um import é válido para análise de dependências.

    Rejeita:
    - Imports que começam com underscore (ex: _pytest, _internal)
    - Módulos nativos do Python (stdlib)
    - Módulos Próprios do Projeto-Alvo (nunca são Fantasmas)

    Args:
        module_name: Nome do módulo importado (em lowercase)
        own_modules: Módulos Próprios inferidos do layout do Projeto-Alvo

    Returns:
        True se o import é válido, False caso contrário
    """
    # Rejeitar imports que começam com underscore
    if module_name.startswith("_"):
        return False

    # Rejeitar módulos nativos do Python
    if module_name in PYTHON_STDLIB_MODULES:
        return False

    # Rejeitar Módulos Próprios: são do Projeto-Alvo, não do PyPI
    if own_modules and module_name in own_modules:
        return False

    return True


def _collect_imports_from_tree(
    tree: ast.AST, imports: Set[str], own_modules: Set[str] | None
) -> None:
    """
    Coleta os Imports Raiz válidos de uma AST no conjunto acumulador.

    Percorre toda a árvore (não só o topo), então imports indentados — dentro de
    `try:`, funções, `if`, `with` — também são coletados.

    Args:
        tree: AST do código (ou de uma linha isolada, no fallback).
        imports: Conjunto acumulador, alterado in-place com os Imports Raiz.
        own_modules: Módulos Próprios inferidos do layout do Projeto-Alvo.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0].lower()
                if is_valid_import(root_module, own_modules):
                    imports.add(root_module)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:  # Ignorar relative imports
                root_module = node.module.split(".")[0].lower()
                if is_valid_import(root_module, own_modules):
                    imports.add(root_module)


def extract_imports_from_code(code: str, own_modules: Set[str] | None = None) -> Set[str]:
    """
    Extrai nomes de módulos importados de um código Python.

    Analisa o código usando AST e extrai:
    - import xxx
    - from xxx import yyy
    - from xxx.yyy import zzz

    Normaliza para o nome do pacote raíz (ex: "django.core" → "django")
    Filtra imports inválidos (comecoam com _, módulos stdlib, Módulos Próprios)

    Args:
        code: Código Python em formato string
        own_modules: Módulos Próprios inferidos do layout do Projeto-Alvo

    Returns:
        Conjunto de nomes de módulos únicos
    """
    imports = set()

    try:
        # Caso normal: o arquivo é Python válido; um parse do arquivo inteiro
        # enxerga imports em qualquer nível de indentação.
        _collect_imports_from_tree(ast.parse(code), imports, own_modules)
    except SyntaxError:
        # Fallback para arquivo não-parseável (ex.: Python 2): recupera o que der,
        # linha a linha, salvando imports antes do primeiro erro de sintaxe.
        for line in code.split("\n"):
            try:
                _collect_imports_from_tree(ast.parse(line), imports, own_modules)
            except SyntaxError:
                continue

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

    # Módulos Próprios saem do layout do próprio archive, sem I/O extra
    archive_paths = _normalize_paths(
        [get_file_path_from_archive_member(member) for member in file_list]
    )
    own_modules = infer_own_modules(_strip_project_root(archive_paths))

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
        imports = extract_imports_from_code(content, own_modules)
        all_imports.update(imports)

    # Converter para lista de dicionários padronizada
    result = []
    for import_name in sorted(all_imports):
        result.append(
            {
                "Pacote": import_name,
                "Versão Usada": "N/A",
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
