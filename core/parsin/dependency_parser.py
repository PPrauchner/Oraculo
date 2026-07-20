"""
Módulo responsável por normalizar e estruturar dependências declaradas.

Recebe a saída processada de readers.py (lista de dicts com Pacote, Versão Usada
e Origem) e retorna uma lista padronizada com a estrutura completa incluindo:
- Pacote
- Versão Usada
- Versão Pypi (inicialmente "N/A")
- Status (inicialmente "Desconhecido")
- Origem (Produção quando não informada)

Entrada:
- Lista de dicionários processada por readers.py

Saída:
- Lista de dicionários padronizada com estrutura completa
"""

from typing import Dict, List, Optional
from utils.constants import ORIGIN_PRODUCTION
from utils.types import DeclarationEntry, Dependency
from utils.functions import READERS
from core.ingestion.filter import is_path_in_ignored_folders

def normalize_dependency(dep: DeclarationEntry) -> Optional[Dependency]:
    """
    Normaliza um dicionário de dependência individual.

    Recebe um dict com 'Pacote' e 'Versão Usada' e retorna um dict
    padronizado com todos os campos obrigatórios.

    A Origem é preservada: é ela que permite isentar Dependências de
    Desenvolvimento da classificação Zumbi (ADR-0003). Na ausência dela,
    assume-se Produção — o recorte conservador.

    Args:
        dep: Dicionário com 'Pacote', 'Versão Usada' e, opcionalmente, 'Origem'

    Returns:
        Dicionário padronizado ou None se inválido
    """
    if not isinstance(dep, dict):
        return None

    # Validar campos obrigatórios
    pacote = dep.get("package", "").strip()
    versao_usada = dep.get("Versão Usada", "").strip()

    if not pacote:
        return None

    return {
        "package": pacote,
        "Versão Usada": versao_usada,
        "Versão PyPI": "N/A",
        "Status": "Desconhecido",
        "Origem": dep.get("Origem", ORIGIN_PRODUCTION),
    }


def parse_dependencies(dependencies: List[DeclarationEntry]) -> List[Dependency]:
    """
    Processa uma lista de dependências e retorna lista padronizada.

    Recebe a saída de readers.py (parse_requirements ou parse_uv_lock)
    e retorna uma lista de dependências com estrutura padronizada.

    Args:
        dependencies: Lista de dicients com 'Pacote' e 'Versão Usada'

    Returns:
        Lista de dicionários padronizada com campos: Pacote, Versão Usada, Versão Pypi, Status
    """
    if not dependencies:
        return []

    if not isinstance(dependencies, list):
        return []

    normalized = []
    for dep in dependencies:
        normalized_dep = normalize_dependency(dep)
        if normalized_dep:
            normalized.append(normalized_dep)

    return normalized


def parse_dependencies_with_filter(
    dependencies: List[DeclarationEntry], file_path: str, ignore_folders: List[str]
) -> List[Dependency]:
    """
    Processa dependências com filtro por pasta ignorada.

    Se o arquivo de origem está em uma pasta ignorada, retorna lista vazia.
    Caso contrário, processa e retorna as dependências normalizadas.

    Args:
        dependencies: Lista de dicts com 'Pacote' e 'Versão Usada'
        file_path: Caminho do arquivo de origem (ex: "tests/requirements.txt")
        ignore_folders: Lista de pastas a ignorar (ex: ["tests", "docs"])

    Returns:
        Lista vazia se arquivo está em pasta ignorada, senão lista normalizada
    """
    

    if is_path_in_ignored_folders(file_path, ignore_folders):
        return []

    return parse_dependencies(dependencies)
