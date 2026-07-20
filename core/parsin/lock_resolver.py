"""
Resolve a Versão Usada de cada pacote do conjunto a partir do Lock.

Responsabilidades:
- Ler o Lock (uv.lock, poetry.lock) do Projeto-Alvo, quando existir, e mapear cada
  Nome de Distribuição normalizado à sua versão exata.
- Sobrescrever a Versão Usada dos pacotes que já estão no conjunto auditado com a
  versão do Lock, casando por Nome de Distribuição normalizado.

O Lock resolve versões, não define o conjunto (ADR-0002): pacotes que só existem no
Lock (transitivas) não entram no conjunto — apenas emprestam versão aos que já estão
nele. Por isso a resolução percorre o conjunto, nunca o Lock.
"""

from core.analysis.name_matching import normalize_name
from core.ingestion.archive_walker import iter_archive_texts
from core.parsin.declaration_collector import is_lock_filename
from core.parsin.readers import parse_lock


from utils.types import Dependency

def build_lock_version_map(archive, ignore_folders: list[str]) -> dict[str, str]:
    """Mapeia Nome de Distribuição normalizado à versão exata registrada no Lock.

    Lê cada Lock fora das Exclusões e acumula suas versões. O mapa inclui também as
    transitivas do Lock; filtrar o que pertence ao conjunto é responsabilidade de
    `resolve_used_versions`.

    Args:
        archive: Objeto zipfile.ZipFile ou tarfile.TarFile do Projeto-Alvo.
        ignore_folders: Pastas em Exclusão (ex.: ["tests", "docs"]).

    Returns:
        Mapa Nome de Distribuição normalizado -> versão exata. Vazio se não houver
        Lock fora das Exclusões.
    """
    version_map: dict[str, str] = {}

    for _path, content in iter_archive_texts(archive, ignore_folders, is_lock_filename):
        for entry in parse_lock(content):
            version = entry.get("Versão Usada", "")
            if version:
                version_map[normalize_name(entry["package"])] = version

    return version_map


def resolve_used_versions(
    declared: list[Dependency], lock_version_map: dict[str, str]
) -> list[Dependency]:
    """Resolve a Versão Usada de cada pacote do conjunto com a versão do Lock.

    Para cada pacote já no conjunto, se o Lock registra sua versão (casando por Nome
    de Distribuição normalizado), essa versão passa a ser a Versão Usada, ainda que a
    Declaração trouxesse um pin. Pacotes ausentes do Lock mantêm o que a Declaração
    resolveu (pin ou indefinido). Nenhum pacote é acrescentado ao conjunto (ADR-0002).

    Args:
        declared: Conjunto auditado (união das Declarações), normalizado.
        lock_version_map: Mapa Nome de Distribuição normalizado -> versão do Lock.

    Returns:
        O mesmo conjunto, com a Versão Usada resolvida onde o Lock a conhece.
    """
    for dep in declared:
        version = lock_version_map.get(normalize_name(dep["package"]))
        if version:
            dep["Versão Usada"] = version

    return declared
