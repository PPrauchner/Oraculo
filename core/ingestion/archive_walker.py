"""
Percorre o Projeto-Alvo entregando o conteúdo dos arquivos que interessam.

Responsabilidades:
- Iterar os caminhos do Projeto-Alvo, seja ele archive ou diretório.
- Descartar o que está em Exclusão e o que o chamador não pediu.
- Ler como texto apenas os arquivos que passaram pelo filtro.

Deriva das duas primitivas de `core.ingestion.source` (ADR-0006) em vez de
reimplementá-las: quem lê Declarações e Lock pede caminho + conteúdo e não conhece
a espécie da fonte.
"""

from typing import Callable, Iterator

from core.ingestion.filter import is_path_in_ignored_folders
from core.ingestion.source import list_paths, read_text


def iter_archive_texts(
    source, ignore_folders: list[str], keep: Callable[[str], bool]
) -> Iterator[tuple[str, str]]:
    """Percorre o Projeto-Alvo e devolve (caminho, conteúdo) dos arquivos pedidos.

    Só os arquivos aprovados por `keep` são lidos: percorrer o índice da fonte é
    barato, decodificar cada arquivo não.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).
        ignore_folders: Pastas em Exclusão (ex.: ["tests", "docs"]).
        keep: Decide, pelo caminho, se o arquivo interessa ao chamador.

    Yields:
        Pares (caminho, conteúdo) dos arquivos fora das Exclusões que `keep`
        aprovou e que puderam ser lidos como texto.
    """
    for file_path in list_paths(source):
        if is_path_in_ignored_folders(file_path, ignore_folders):
            continue

        if not keep(file_path):
            continue

        content = read_text(source, file_path)
        if content is None:
            continue

        yield file_path, content
