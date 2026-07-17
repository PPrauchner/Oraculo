"""
Reúne o conjunto auditado a partir da união de todas as Declarações.

Responsabilidades:
- Percorrer o Projeto-Alvo e ler cada Declaração fora das Exclusões.
- Unir os pacotes declarados deduplicando por Nome de Distribuição.
- Excluir o Lock do conjunto: ele resolve versões, não o define (ADR-0002).

O Lock (uv.lock, poetry.lock) lista centenas de transitivas que ninguém importa;
lê-lo como Declaração faria toda transitiva virar Zumbi. Por isso o conjunto vem
só das Declarações; o Lock entra depois, para resolver a Versão Usada.
"""

from typing import Callable, Dict, List

from utils.constants import LOCK_EXTENSION
from utils.functions import READERS
from core.ingestion.decompressor import get_archive_files
from core.ingestion.filter import is_path_in_ignored_folders
from core.parsin.dependency_parser import parse_dependencies

# Popular o registry de READERS: o decorador `registrar` só roda quando o módulo
# é importado (ver utils/functions.py).
import core.parsin.readers  # noqa: F401


def is_lock_filename(file_name: str) -> bool:
    """Indica se um arquivo é um Lock (uv.lock, poetry.lock).

    O Lock resolve versões, não define o conjunto auditado (ADR-0002), então é
    ignorado ao montar o conjunto.

    Args:
        file_name: Nome ou caminho do arquivo.

    Returns:
        True se o arquivo for um Lock, False caso contrário.
    """
    return file_name.lower().endswith(LOCK_EXTENSION)


def _match_declaration_reader(file_name: str) -> Callable[[str], list] | None:
    """Devolve o reader de uma Declaração, ou None se o arquivo não for uma.

    O Lock casa com o reader `.lock`, mas nunca define o conjunto (ADR-0002), então
    é descartado antes de consultar o registry.

    Args:
        file_name: Nome ou caminho do arquivo.

    Returns:
        A função de leitura registrada para a Declaração, ou None.
    """
    lower = file_name.lower()
    if is_lock_filename(lower):
        return None

    for extension, reader in READERS.items():
        if lower.endswith(extension):
            return reader
    return None


def _read_member(archive, member) -> str | None:
    """Lê o conteúdo textual de um membro de ZIP ou TAR.

    Args:
        archive: Objeto zipfile.ZipFile ou tarfile.TarFile.
        member: Membro do archive (ZipInfo ou TarInfo).

    Returns:
        Conteúdo do arquivo como texto, ou None se não puder ser lido.
    """
    try:
        if hasattr(member, "filename"):  # zipfile
            return archive.read(member.filename).decode("utf-8", errors="ignore")

        extracted = archive.extractfile(member)  # tarfile
        if extracted is None:
            return None
        return extracted.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def merge_declarations(dependencies: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Une Declarações deduplicando por Nome de Distribuição.

    Um pacote declarado em mais de uma Declaração aparece uma única vez, com a
    Origem da primeira ocorrência preservada (ADR-0002).

    Args:
        dependencies: Dependências normalizadas, possivelmente com repetições.

    Returns:
        Lista sem duplicatas, na ordem da primeira ocorrência de cada pacote.
    """
    seen = set()
    merged = []
    for dep in dependencies:
        key = dep["Pacote"].lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(dep)
    return merged


def collect_declarations(archive, ignore_folders: List[str]) -> List[Dict[str, str]]:
    """Monta o conjunto auditado como a união de todas as Declarações.

    Percorre o archive e, para cada Declaração fora das Exclusões, acumula seus
    pacotes. O Lock é ignorado (ADR-0002). O resultado é deduplicado por Nome de
    Distribuição, preservando a Origem de cada pacote.

    Args:
        archive: Objeto zipfile.ZipFile ou tarfile.TarFile do Projeto-Alvo.
        ignore_folders: Pastas em Exclusão (ex.: ["tests", "docs"]).

    Returns:
        Conjunto auditado como lista de dependências normalizadas. Vazio se o
        Projeto-Alvo não tiver nenhuma Declaração fora das Exclusões.
    """
    declared: List[Dict[str, str]] = []

    for member in get_archive_files(archive):
        file_path = getattr(member, "filename", None) or getattr(member, "name", None)
        if not file_path:
            continue

        if is_path_in_ignored_folders(file_path, ignore_folders):
            continue

        reader = _match_declaration_reader(file_path)
        if reader is None:
            continue

        content = _read_member(archive, member)
        if content is None:
            continue

        declared.extend(parse_dependencies(reader(content)))

    return merge_declarations(declared)
