import pytest
from core.report.normalization import normalize, build_export_rows, filter_export_rows
from utils.constants import (
    CATEGORY_HEALTHY,
    CATEGORY_ZOMBIE,
    CATEGORY_GHOST,
    OUTDATED_YES,
    OUTDATED_NO,
    ORIGIN_PRODUCTION,
    ORIGIN_DEVELOPMENT,
    VERSION_UNAVAILABLE,
)

EXPORT_SCHEMA = [
    "Data da Análise",
    "Projeto",
    "package",
    "Categoria",
    "origin",
    "used_version",
    "pypi_version",
    "Desatualizada",
    "Tamanho",
    "Idade",
]

def test_normalize_with_valid_data():
    """Verifica se a lista de dicionários é montada corretamente com dados válidos."""
    input_data = [
        {
            "package": "pandas",
            "used_version": "1.5.0",
            "pypi_version": "2.0.0",
            "status": "Desatualizado",
            "Tamanho": 2 * 1024 * 1024,
            "Idade": 30,
            "origin": "Production",
            "Extra": "Deveria ser ignorado"
        }
    ]

    expected = [
        {
            "package": "pandas",
            "used_version": "1.5.0",
            "pypi_version": "2.0.0",
            "status": "Desatualizado",
            "Tamanho": "2.0 MB",
            "Idade": "30 dias",
            "origin": "Production",
        }
    ]

    result = normalize(input_data)
    assert result == expected
    assert "Extra" not in result[0]

def test_normalize_with_missing_keys():
    """Verifica se o código lida com dicionários incompletos usando 'N/A'."""
    input_data = [{"package": "numpy"}] # Faltam versões e status
    
    result = normalize(input_data)
    
    assert result[0]["used_version"] == "N/A"
    assert result[0]["status"] == "Desconhecido"

def test_normalize_empty_list():
    """Verifica o retorno padrão quando a lista de entrada está vazia."""
    result = normalize([])
    
    assert len(result) == 1
    assert result[0]["package"] == "N/A"
    assert result[0]["status"] == "N/A"

def test_normalize_multiple_items():
    """Garante que a função processa múltiplos itens na lista."""
    input_data = [
        {"package": "pkg1", "status": "OK"},
        {"package": "pkg2", "status": "Erro"}
    ]

    result = normalize(input_data)
    assert len(result) == 2
    assert result[0]["package"] == "pkg1"
    assert result[1]["package"] == "pkg2"

def test_normalize_surfaces_origin():
    """O relatório distingue Produção de Desenvolvimento expondo a Origem."""
    input_data = [
        {"package": "requests", "origin": "Production"},
        {"package": "pytest", "origin": "Development"},
    ]

    result = normalize(input_data)

    assert result[0]["origin"] == "Production"
    assert result[1]["origin"] == "Development"

def test_normalize_missing_origin_defaults_na():
    """Sem Origem informada, o relatório mostra 'N/A' em vez de quebrar."""
    result = normalize([{"package": "numpy"}])

    assert result[0]["origin"] == "N/A"


def test_normalize_formats_tamanho_as_readable_units():
    """Tamanho cru (bytes) vira unidade legível (KB/MB) na tabela."""
    input_data = [
        {"package": "big", "Tamanho": 2 * 1024 * 1024, "origin": "Production"},
        {"package": "small", "Tamanho": 500 * 1024, "origin": "Production"},
    ]

    result = normalize(input_data)

    assert result[0]["Tamanho"] == "2.0 MB"
    assert result[1]["Tamanho"] == "500.0 KB"


def test_normalize_formats_idade_in_days():
    """Idade crua (dias inteiros) é exibida em dias."""
    input_data = [{"package": "pkg", "Idade": 30, "origin": "Production"}]

    result = normalize(input_data)

    assert result[0]["Idade"] == "30 dias"


def test_normalize_tamanho_idade_indisponivel_pass_through():
    """Tamanho/Idade indisponíveis (N/D) permanecem N/D, nunca 0."""
    input_data = [
        {"package": "pkg", "Tamanho": "N/D", "Idade": "N/D", "origin": "Production"}
    ]

    result = normalize(input_data)

    assert result[0]["Tamanho"] == "N/D"
    assert result[0]["Idade"] == "N/D"


def test_normalize_missing_tamanho_idade_defaults_indisponivel():
    """Sem Tamanho/Idade informados, exibe indisponível em vez de quebrar."""
    result = normalize([{"package": "numpy", "origin": "Production"}])

    assert result[0]["Tamanho"] == "N/D"
    assert result[0]["Idade"] == "N/D"


def test_normalize_ghost_marks_reference_as_latest_version():
    """Fantasma (sem Origem) explicita que Tamanho/Idade são da versão mais recente."""
    ghost = [{"package": "requests", "Tamanho": 1024 * 1024, "Idade": 5}]

    result = normalize(ghost)

    assert "última versão" in result[0]["Tamanho"]
    assert "última versão" in result[0]["Idade"]


# ============ build_export_rows (esquema de exportação US-06/US-07) ============


def test_export_rows_follow_schema_one_row_per_dependency():
    """Cada dependência vira uma linha com exatamente as colunas do esquema, na ordem."""
    dependencies = [
        {
            "package": "pandas",
            "origin": ORIGIN_PRODUCTION,
            "used_version": "1.5.0",
            "pypi_version": "2.0.0",
            "status": "Desatualizado",
            "Tamanho": 2 * 1024 * 1024,
            "Idade": 30,
        }
    ]

    rows = build_export_rows(
        dependencies, zombies=[], ghosts=[],
        project_name="grupo-03", analysis_date="2026-07-18",
    )

    assert len(rows) == 1
    assert list(rows[0].keys()) == EXPORT_SCHEMA
    assert rows[0]["Data da Análise"] == "2026-07-18"
    assert rows[0]["Projeto"] == "grupo-03"
    assert rows[0]["package"] == "pandas"
    assert rows[0]["Categoria"] == CATEGORY_HEALTHY


def test_export_rows_zombie_and_outdated_share_a_single_row():
    """Zumbi e Desatualizada convivem: uma linha, Categoria Zumbi e Desatualizada marcada."""
    dependency = {
        "package": "altair",
        "origin": ORIGIN_PRODUCTION,
        "used_version": "4.0.0",
        "pypi_version": "5.2.0",
        "status": "Desatualizado",
        "Tamanho": 512 * 1024,
        "Idade": 400,
    }

    rows = build_export_rows(
        [dependency],
        zombies=[dependency],
        ghosts=[],
        project_name="grupo-03",
        analysis_date="2026-07-18",
    )

    assert len(rows) == 1
    assert rows[0]["Categoria"] == CATEGORY_ZOMBIE
    assert rows[0]["Desatualizada"] == OUTDATED_YES


def test_export_rows_categorize_zombie_ghost_and_healthy():
    """Categoria estratifica as três classes da auditoria."""
    zombie = {"package": "altair", "origin": ORIGIN_PRODUCTION, "status": "Atualizado"}
    ghost = {"package": "requests", "status": "Atualizado"}
    healthy = {"package": "streamlit", "origin": ORIGIN_PRODUCTION, "status": "Atualizado"}

    rows = build_export_rows(
        [zombie, ghost, healthy],
        zombies=[zombie],
        ghosts=[ghost],
        project_name="grupo-03",
        analysis_date="2026-07-18",
    )

    categories = {row["package"]: row["Categoria"] for row in rows}

    assert categories == {
        "altair": CATEGORY_ZOMBIE,
        "requests": CATEGORY_GHOST,
        "streamlit": CATEGORY_HEALTHY,
    }


def test_export_rows_origin_separates_production_from_development():
    """Origem distingue Produção de Desenvolvimento; Fantasma não tem Declaração."""
    production = {"package": "streamlit", "origin": ORIGIN_PRODUCTION}
    development = {"package": "ruff", "origin": ORIGIN_DEVELOPMENT}
    ghost = {"package": "requests"}

    rows = build_export_rows(
        [production, development, ghost],
        zombies=[],
        ghosts=[ghost],
        project_name="grupo-03",
        analysis_date="2026-07-18",
    )

    origins = {row["package"]: row["origin"] for row in rows}

    assert origins["streamlit"] == ORIGIN_PRODUCTION
    assert origins["ruff"] == ORIGIN_DEVELOPMENT
    assert origins["requests"] == "N/A"


def test_export_rows_keep_size_and_age_raw_or_unavailable():
    """Tamanho e Idade saem crus para diffing; sem Versão Usada, N/D — nunca 0."""
    with_metrics = {"package": "streamlit", "Tamanho": 2048, "Idade": 15}
    without_metrics = {"package": "ruff"}

    rows = build_export_rows(
        [with_metrics, without_metrics],
        zombies=[],
        ghosts=[],
        project_name="grupo-03",
        analysis_date="2026-07-18",
    )

    assert rows[0]["Tamanho"] == 2048
    assert rows[0]["Idade"] == 15
    assert rows[1]["Tamanho"] == VERSION_UNAVAILABLE
    assert rows[1]["Idade"] == VERSION_UNAVAILABLE


def test_export_rows_do_not_duplicate_a_dependency():
    """Uma dependência classificada em mais de uma lista ainda produz uma única linha."""
    zombie_and_outdated = {
        "package": "altair",
        "origin": ORIGIN_PRODUCTION,
        "status": "Desatualizado",
    }

    rows = build_export_rows(
        [zombie_and_outdated],
        zombies=[zombie_and_outdated],
        ghosts=[],
        project_name="grupo-03",
        analysis_date="2026-07-18",
    )

    packages = [row["package"] for row in rows]

    assert len(packages) == len(set(packages)) == 1


def test_export_rows_distinguish_two_analyses_of_the_same_project():
    """A Data da Análise dá o eixo temporal da US-07: mesmo projeto, execuções distintas."""
    dependencies = [{"package": "streamlit", "origin": ORIGIN_PRODUCTION}]

    first = build_export_rows(
        dependencies, [], [], project_name="grupo-03", analysis_date="2026-07-11"
    )
    second = build_export_rows(
        dependencies, [], [], project_name="grupo-03", analysis_date="2026-07-18"
    )

    assert first[0]["Data da Análise"] != second[0]["Data da Análise"]
    assert first[0]["Projeto"] == second[0]["Projeto"]


# ============ filter_export_rows (seleção de categorias na exportação) ============


def _sample_export_rows() -> list[dict]:
    """Linhas de exportação cobrindo Zumbi+Desatualizada, Fantasma e Saudável."""
    zombie = {"package": "altair", "origin": ORIGIN_PRODUCTION, "status": "Desatualizado"}
    ghost = {"package": "requests", "status": "Atualizado"}
    healthy = {"package": "streamlit", "origin": ORIGIN_PRODUCTION, "status": "Atualizado"}

    return build_export_rows(
        [zombie, ghost, healthy],
        zombies=[zombie],
        ghosts=[ghost],
        project_name="grupo-03",
        analysis_date="2026-07-18",
    )


def test_filter_selects_only_the_chosen_categories():
    """Selecionar Zumbis exporta só as linhas de Categoria Zumbi."""
    rows = filter_export_rows(_sample_export_rows(), {CATEGORY_ZOMBIE}, False)

    assert [row["package"] for row in rows] == ["altair"]


def test_filter_selects_outdated_regardless_of_category():
    """Desatualizadas não é Categoria: seleciona pela coluna própria."""
    rows = filter_export_rows(_sample_export_rows(), set(), True)

    assert [row["package"] for row in rows] == ["altair"]
    assert rows[0]["Categoria"] == CATEGORY_ZOMBIE


def test_filter_does_not_duplicate_a_row_matched_twice():
    """Zumbi e Desatualizada selecionadas juntas ainda exportam uma única linha."""
    rows = filter_export_rows(_sample_export_rows(), {CATEGORY_ZOMBIE}, True)

    assert [row["package"] for row in rows] == ["altair"]


def test_filter_with_all_categories_keeps_every_row():
    """Selecionar todas as categorias exporta o conjunto auditado inteiro."""
    every_row = _sample_export_rows()
    rows = filter_export_rows(
        every_row, {CATEGORY_ZOMBIE, CATEGORY_GHOST, CATEGORY_HEALTHY}, True
    )

    assert rows == every_row
