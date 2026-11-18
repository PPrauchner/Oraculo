"""
O Projeto de Exemplo passado pelo pipeline de `core/`, com o PyPI substituído.

Quem abre o ORÁCULO para conhecê-lo raramente tem um projeto Python à mão: o exemplo
é o que mostra o relatório inteiro num clique (issue #58). Ele só cumpre esse papel
se o relatório que produz tiver todas as Categorias e uma Desatualizada.

Responsabilidades:
- Guardar que o exemplo produz Zumbi, Fantasma, Saudável e Desatualizada.
- Guardar que o Lock do exemplo resolve a Versão Usada de toda Dependência Declarada.
- Guardar que o exemplo é dado em memória, válido como Projeto-Alvo.
"""

import pytest

from core.analysis.ghost_analizer import analyze_ghost_dependencies
from core.analysis.outdated_analizer import analyze_dependency_status
from core.analysis.zombie_analizer import analyze_zombie_dependencies
from core.ingestion.filter import validate_project_structure
from core.ingestion.sample_project import SAMPLE_PROJECT_NAME, sample_project
from core.parsin.declaration_collector import collect_declarations
from core.parsin.import_parser import parse_imports_with_filter
from core.parsin.lock_resolver import build_lock_version_map, resolve_used_versions
from core.report.normalization import build_export_rows
from utils.constants import (
    CATEGORY_GHOST,
    CATEGORY_HEALTHY,
    CATEGORY_ZOMBIE,
    OUTDATED_YES,
    UNKNOWN,
)

# Versão "mais recente" do dublê: maior que qualquer versão que o exemplo fixa.
LATEST = "99.0.0"


def _fake_pypi(package_name: str) -> dict:
    """Metadado mínimo do PyPI, determinístico e sem rede."""
    return {"info": {"version": LATEST}, "releases": {}}


@pytest.fixture
def audited(monkeypatch):
    """O exemplo auditado pelas mesmas etapas que `pages/loading.py` encadeia."""
    monkeypatch.setattr(
        "core.analysis.outdated_analizer.fetch_package_data", _fake_pypi
    )

    source = sample_project()
    declared = collect_declarations(source, [])
    declared = resolve_used_versions(declared, build_lock_version_map(source, []))
    imports = parse_imports_with_filter(source, [])
    zombies = analyze_zombie_dependencies(declared, imports)
    ghosts = analyze_ghost_dependencies(declared, imports)
    dependencies = analyze_dependency_status(declared + ghosts)

    return declared, build_export_rows(
        dependencies, zombies, ghosts, SAMPLE_PROJECT_NAME, "2026-01-01T00:00:00"
    )


def test_the_sample_is_a_valid_target_project():
    """Sem upload e sem diretório, o exemplo passa na mesma validação de qualquer fonte."""
    assert validate_project_structure(sample_project(), []) == (True, None)


def test_the_sample_shows_every_category_and_an_outdated_one(audited):
    """O relatório do exemplo só demonstra a ferramenta se mostrar tudo o que ela acha."""
    _, rows = audited
    categories = {row["category"] for row in rows}

    assert {CATEGORY_ZOMBIE, CATEGORY_GHOST, CATEGORY_HEALTHY} <= categories
    assert any(row["outdated"] == OUTDATED_YES for row in rows)


def test_the_lock_resolves_every_declared_dependency(audited):
    """Sem Versão Usada, Tamanho e Idade sairiam Indeterminados no exemplo."""
    declared, _ = audited

    assert declared
    assert all(dep["used_version"] not in ("", UNKNOWN) for dep in declared)


def test_each_call_hands_out_its_own_copy():
    """A fonte vai para `session_state`: mexer numa cópia não altera o exemplo."""
    first = sample_project()
    first.clear()

    assert sample_project()
