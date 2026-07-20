"""
Módulo responsável por extrair imports do código-fonte.

Analisa arquivos Python utilizando AST (Abstract Syntax Tree)
para identificar dependências realmente utilizadas no código.

Entrada:
- Fonte do Projeto-Alvo (archive ou diretório), via core.ingestion.source
- Pastas em Exclusão

Saída:
- Lista de dicionários com imports encontrados:
  {
    "package": "nome_do_modulo",
    "used_version": "N/A",
    "Versão Pypi": "N/A",
    "status": "Desconhecido"
  }
"""

import ast

from core.ingestion.filter import is_path_in_ignored_folders
from core.ingestion.source import ProjectSource, list_paths, read_text
from utils.constants import PYTHON_STDLIB_MODULES
from utils.types import Dependency

# Pasta que apenas embrulha os Módulos Próprios num layout `src/`
SRC_LAYOUT_FOLDER = "src"


def infer_own_modules(file_paths: list[str]) -> set[str]:
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


def is_valid_import(module_name: str, own_modules: set[str] | None = None) -> bool:
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
    tree: ast.AST, imports: set[str], own_modules: set[str] | None
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


def extract_imports_from_code(code: str, own_modules: set[str] | None = None) -> set[str]:
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


def parse_imports(
    source: ProjectSource, ignore_folders: list[str]
) -> list[Dependency]:
    """
    Extrai os Imports Raiz de todos os arquivos Python do Projeto-Alvo.

    Itera pelos arquivos Python, respeita as Exclusões, extrai imports e retorna
    lista padronizada.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).
        ignore_folders: Pastas em Exclusão (ex.: ["tests", "docs"]).

    Returns:
        Lista de dicionários com imports encontrados
    """
    if source is None:
        return []

    all_imports = set()

    # Os caminhos já vêm relativos à raiz do Projeto-Alvo, então os Módulos
    # Próprios saem do layout, sem I/O extra.
    file_paths = list_paths(source)
    own_modules = infer_own_modules(file_paths)

    for file_path in file_paths:
        # Verificar se arquivo está em uma Exclusão
        if is_path_in_ignored_folders(file_path, ignore_folders):
            continue

        # Processar apenas arquivos .py
        if not file_path.endswith(".py"):
            continue

        # Ler conteúdo
        content = read_text(source, file_path)
        if content is None:
            continue

        # Extrair imports
        imports = extract_imports_from_code(content, own_modules)
        all_imports.update(imports)

    # Converter para lista de dicionários padronizada
    result: list[Dependency] = []
    for import_name in sorted(all_imports):
        result.append(
            {
                "package": import_name,
                "used_version": "N/A",
                "pypi_version": "N/A",
                "status": "Desconhecido",
            }
        )

    return result


def parse_imports_with_filter(
    source: ProjectSource, ignore_folders: list[str]
) -> list[Dependency]:
    """
    Wrapper para parse_imports com validação de entrada.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).
        ignore_folders: Pastas em Exclusão

    Returns:
        Lista de imports padronizada
    """
    return parse_imports(source, ignore_folders or [])
