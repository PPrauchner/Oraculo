from core.report.statistics import (
    format_summary_lines,
    summarize_by_category,
    summarize_category,
)
from utils.constants import ORIGIN_PRODUCTION, VERSION_UNAVAILABLE


def test_category_sums_size_and_averages_age():
    """A categoria soma o Tamanho de suas dependências e faz a média da Idade."""
    dependencies = [
        {"package": "pandas", "Origem": ORIGIN_PRODUCTION, "Tamanho": 1024, "Idade": 10},
        {"package": "plotly", "Origem": ORIGIN_PRODUCTION, "Tamanho": 3072, "Idade": 20},
    ]

    summary = summarize_category(dependencies)

    assert summary["Quantidade"] == 2
    assert summary["Tamanho Total"] == 4096
    assert summary["Idade Média"] == 15


def test_unavailable_metrics_stay_out_of_the_aggregations():
    """Sem Versão Usada, Tamanho/Idade são N/D: não entram na soma nem na média."""
    dependencies = [
        {"package": "pandas", "Origem": ORIGIN_PRODUCTION, "Tamanho": 1024, "Idade": 10},
        {
            "package": "ruff",
            "Origem": ORIGIN_PRODUCTION,
            "Tamanho": VERSION_UNAVAILABLE,
            "Idade": VERSION_UNAVAILABLE,
        },
    ]

    summary = summarize_category(dependencies)

    assert summary["Tamanho Total"] == 1024
    assert summary["Idade Média"] == 10


def test_excluded_dependencies_are_counted_so_the_average_is_not_misleading():
    """Quantidade conta todas; a exclusão do N/D fica contabilizada, não escondida."""
    dependencies = [
        {"package": "pandas", "Origem": ORIGIN_PRODUCTION, "Tamanho": 1024, "Idade": 10},
        {
            "package": "ruff",
            "Origem": ORIGIN_PRODUCTION,
            "Tamanho": VERSION_UNAVAILABLE,
            "Idade": VERSION_UNAVAILABLE,
        },
    ]

    summary = summarize_category(dependencies)

    assert summary["Quantidade"] == 2
    assert summary["Sem Tamanho"] == 1
    assert summary["Sem Idade"] == 1


def test_empty_category_reports_unavailable_instead_of_dividing_by_zero():
    """Categoria vazia (ex.: nenhum Zumbi) é estado vazio, não erro."""
    summary = summarize_category([])

    assert summary["Quantidade"] == 0
    assert summary["Tamanho Total"] is None
    assert summary["Idade Média"] is None
    assert summary["Sem Tamanho"] == 0
    assert summary["Sem Idade"] == 0


def test_category_without_any_measured_metric_reports_unavailable():
    """Se ninguém tem Versão Usada resolvida, não há soma nem média a exibir."""
    dependencies = [
        {
            "package": "ruff",
            "Origem": ORIGIN_PRODUCTION,
            "Tamanho": VERSION_UNAVAILABLE,
            "Idade": VERSION_UNAVAILABLE,
        }
    ]

    summary = summarize_category(dependencies)

    assert summary["Quantidade"] == 1
    assert summary["Tamanho Total"] is None
    assert summary["Idade Média"] is None
    assert summary["Sem Tamanho"] == 1


# ============ summarize_by_category (estratificação por Categoria) ============


def test_statistics_are_stratified_per_category():
    """Cada categoria do relatório ganha suas próprias estatísticas."""
    zombie = {"package": "altair", "Origem": ORIGIN_PRODUCTION, "Tamanho": 512, "Idade": 400}
    healthy = {
        "package": "streamlit",
        "Origem": ORIGIN_PRODUCTION,
        "Tamanho": 1024,
        "Idade": 10,
    }
    report = {
        "Todas as Dependências": [zombie, healthy],
        "Zumbis": [zombie],
        "Fantasmas": [],
    }

    summaries = summarize_by_category(report)

    assert summaries["Todas as Dependências"]["Tamanho Total"] == 1536
    assert summaries["Zumbis"]["Tamanho Total"] == 512
    assert summaries["Zumbis"]["Idade Média"] == 400
    assert summaries["Fantasmas"]["Quantidade"] == 0


def test_statistics_agree_with_the_category_tables():
    """A Quantidade de cada categoria bate com a lista que alimenta sua tabela."""
    report = {
        "Todas as Dependências": [{"package": "a"}, {"package": "b"}, {"package": "c"}],
        "Zumbis": [{"package": "a"}],
        "Desatualizadas": [{"package": "a"}, {"package": "b"}],
    }

    summaries = summarize_by_category(report)

    for category_label, dependencies in report.items():
        assert summaries[category_label]["Quantidade"] == len(dependencies)


def test_a_new_category_is_summarized_without_touching_the_aggregation():
    """Categoria nova entra na estratificação sozinha — nada de lista fixa."""
    report = {"Categoria Inédita": [{"package": "novo", "Tamanho": 2048, "Idade": 7}]}

    summaries = summarize_by_category(report)

    assert list(summaries) == ["Categoria Inédita"]
    assert summaries["Categoria Inédita"]["Tamanho Total"] == 2048


# ============ format_summary_lines (exibição das estatísticas) ============


def test_summary_lines_show_size_in_readable_units_and_age_in_days():
    """Tamanho somado sai em KB/MB; Idade média, em dias."""
    summary = summarize_category(
        [
            {"package": "a", "Tamanho": 1024 * 1024, "Idade": 10},
            {"package": "b", "Tamanho": 1024 * 1024, "Idade": 20},
        ]
    )

    lines = format_summary_lines(summary)

    assert lines == ["Tamanho: 2.0 MB", "Idade média: 15 dias"]


def test_summary_lines_disclose_how_many_dependencies_were_left_out():
    """A média não engana: a linha diz sobre quantas dependências ela foi calculada."""
    summary = summarize_category(
        [
            {"package": "a", "Tamanho": 1024, "Idade": 10},
            {"package": "b", "Tamanho": VERSION_UNAVAILABLE, "Idade": VERSION_UNAVAILABLE},
        ]
    )

    lines = format_summary_lines(summary)

    assert lines == [
        "Tamanho: 1.0 KB (1 de 2 sem dado)",
        "Idade média: 10 dias (1 de 2 sem dado)",
    ]


def test_summary_lines_of_an_empty_category_report_unavailable():
    """Categoria vazia exibe N/D, sem nota de exclusão — não havia o que excluir."""
    lines = format_summary_lines(summarize_category([]))

    assert lines == ["Tamanho: N/D", "Idade média: N/D"]
