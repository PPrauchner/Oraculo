"""
Testes do resolvedor de Versão Usada a partir do Lock.

Cobrem a segunda metade do ADR-0002: o Lock resolve a Versão Usada de cada pacote
do conjunto (por Nome de Distribuição normalizado), mas nunca acrescenta pacotes ao
conjunto auditado.
"""

import io
import zipfile

from core.parsin.declaration_collector import collect_declarations
from core.parsin.lock_resolver import build_lock_version_map, resolve_used_versions


def _zip(files: dict[str, str]) -> zipfile.ZipFile:
    """Monta um ZIP em memória a partir de {caminho: conteúdo}."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    buffer.seek(0)
    return zipfile.ZipFile(buffer)


def test_lock_resolve_versao_usada_do_conjunto():
    """Com Lock presente, a Versão Usada vem da versão exata do Lock (ADR-0002)."""
    declared = [{"package": "requests", "used_version": ""}]

    resolved = resolve_used_versions(declared, {"requests": "2.31.0"})

    assert resolved[0]["used_version"] == "2.31.0"


def test_lock_vence_o_pin_da_declaracao():
    """A versão do Lock resolve a Versão Usada mesmo sobre um pin declarado."""
    declared = [{"package": "requests", "used_version": "2.20.0"}]

    resolved = resolve_used_versions(declared, {"requests": "2.31.0"})

    assert resolved[0]["used_version"] == "2.31.0"


def test_sem_lock_o_pin_permanece_a_versao_usada():
    """Sem Lock, um pin declarado continua sendo a Versão Usada (ADR-0002)."""
    declared = [{"package": "requests", "used_version": "2.31.0"}]

    resolved = resolve_used_versions(declared, {})

    assert resolved[0]["used_version"] == "2.31.0"


def test_sem_lock_sem_pin_a_versao_usada_fica_indefinida():
    """Sem Lock e sem pin, a Versão Usada permanece indefinida (ADR-0002)."""
    declared = [{"package": "requests", "used_version": ""}]

    resolved = resolve_used_versions(declared, {})

    assert resolved[0]["used_version"] == ""


def test_lock_nao_acrescenta_pacotes_ao_conjunto():
    """Transitivas do Lock ausentes do conjunto não são adicionadas (ADR-0002)."""
    declared = [{"package": "requests", "used_version": ""}]
    lock_map = {"requests": "2.31.0", "certifi": "2024.2.2", "urllib3": "2.2.1"}

    resolved = resolve_used_versions(declared, lock_map)

    assert [dep["package"] for dep in resolved] == ["requests"]


def test_join_normaliza_o_nome_de_distribuicao():
    """O casamento Lock↔conjunto normaliza Nome de Distribuição (scikit-learn)."""
    declared = [{"package": "scikit-learn", "used_version": ""}]

    resolved = resolve_used_versions(declared, {"scikit_learn": "1.5.0"})

    assert resolved[0]["used_version"] == "1.5.0"


def test_build_lock_version_map_le_o_lock_do_archive():
    """build_lock_version_map lê o uv.lock e mapeia Nome de Distribuição -> versão."""
    uv_lock = """
[[package]]
name = "requests"
version = "2.31.0"

[[package]]
name = "certifi"
version = "2024.2.2"
"""
    archive = _zip({"pyproject.toml": '[project]\nname="alvo"\n', "uv.lock": uv_lock})

    version_map = build_lock_version_map(archive, ignore_folders=[])

    assert version_map == {"requests": "2.31.0", "certifi": "2024.2.2"}


def test_build_lock_version_map_sem_lock_e_vazio():
    """Sem Lock no archive, o mapa de versões é vazio."""
    archive = _zip({"requirements.txt": "requests==2.31.0\n"})

    assert build_lock_version_map(archive, ignore_folders=[]) == {}


def test_pipeline_lock_resolve_declaracao_nao_pinada_sem_inflar_conjunto():
    """Fim a fim: o Lock resolve a Versão Usada de uma Declaração não pinada e as
    transitivas do Lock não entram no conjunto auditado (ADR-0002)."""
    pyproject = '[project]\nname = "alvo"\ndependencies = ["requests>=2.31"]\n'
    uv_lock = """
[[package]]
name = "requests"
version = "2.31.0"

[[package]]
name = "certifi"
version = "2024.2.2"
"""
    archive = _zip({"pyproject.toml": pyproject, "uv.lock": uv_lock})

    audited = collect_declarations(archive, ignore_folders=[])
    lock_map = build_lock_version_map(archive, ignore_folders=[])
    resolved = resolve_used_versions(audited, lock_map)

    assert [dep["package"] for dep in resolved] == ["requests"]
    assert resolved[0]["used_version"] == "2.31.0"
