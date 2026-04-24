"""
Módulo parsin - Leitura, parsing e normalização de dependências.

Combina:
- readers.py: Extrai dados brutos de requirements.txt e arquivos .lock
- dependency_parser.py: Normaliza e estrutura as dependências
- import_parser.py: Identifica imports usados no código-fonte
- normalization.py: Resolve diferenças entre nomes de pacote e import
"""

from .readers import parse_requirements, parse_lock, parse_environment_yml
from .dependency_parser import (
    parse_dependencies,
    normalize_dependency,
    parse_dependencies_with_filter,
)
from .import_parser import parse_imports, parse_imports_with_filter

__all__ = [
    "parse_requirements",
    "parse_lock",
    "parse_environment_yml",
    "parse_dependencies",
    "normalize_dependency",
    "parse_dependencies_with_filter",
    "parse_imports",
    "parse_imports_with_filter",
]
