"""
Percorre o Projeto-Alvo entregando o conteúdo dos arquivos que interessam.

Responsabilidades:
- Iterar os membros do archive (ZIP ou TAR) por caminho, sem extrair para o disco.
- Descartar o que está em Exclusão e o que o chamador não pediu.
- Ler como texto apenas os arquivos que passaram pelo filtro.

Ponto único de acoplamento ao archive para quem lê Declarações e Lock: esses módulos
pedem caminho + conteúdo e não conhecem ZipInfo/TarInfo. O ADR-0001 assume esse
acoplamento como o custo da ingestão dupla; concentrá-lo aqui é o que mantém o custo
em um lugar só.
"""

from typing import Callable, Iterator

from core.ingestion.decompressor import get_archive_files
from core.ingestion.filter import is_path_in_ignored_folders


def _member_path(member) -> str:
    """Caminho de um membro de ZIP (`filename`) ou de TAR (`name`).

    Args:
        member: Membro do archive (ZipInfo ou TarInfo).

    Returns:
        O caminho do arquivo, ou "" se o membro não expuser nenhum.
    """
    return getattr(member, "filename", None) or getattr(member, "name", None) or ""


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


def iter_archive_texts(
    archive, ignore_folders: list[str], keep: Callable[[str], bool]
) -> Iterator[tuple[str, str]]:
    """Percorre o archive e devolve (caminho, conteúdo) dos arquivos pedidos.

    Só os arquivos aprovados por `keep` são lidos: percorrer o índice do archive é
    barato, decodificar cada arquivo não.

    Args:
        archive: Objeto zipfile.ZipFile ou tarfile.TarFile do Projeto-Alvo.
        ignore_folders: Pastas em Exclusão (ex.: ["tests", "docs"]).
        keep: Decide, pelo caminho, se o arquivo interessa ao chamador.

    Yields:
        Pares (caminho, conteúdo) dos arquivos fora das Exclusões que `keep`
        aprovou e que puderam ser lidos como texto.
    """
    for member in get_archive_files(archive):
        file_path = _member_path(member)
        if not file_path:
            continue

        if is_path_in_ignored_folders(file_path, ignore_folders):
            continue

        if not keep(file_path):
            continue

        content = _read_member(archive, member)
        if content is None:
            continue

        yield file_path, content
