from core.report.statistics import (
    summarize_by_category,
    summarize_category,
    summary_metrics,
)
from utils.constants import ORIGIN_PRODUCTION, UNKNOWN


def test_category_sums_size_and_averages_age():
    """A categoria soma o Tamanho de suas dependências e faz a média da Idade."""
    dependencies = [
        {"package": "pandas", "origin": ORIGIN_PRODUCTION, "size": 1024, "age": 10},
        {"package": "plotly", "origin": ORIGIN_PRODUCTION, "size": 3072, "age": 20},
    ]

    summary = summarize_category(dependencies)

    assert summary["count"] == 2
    assert summary["total_size"] == 4096
    assert summary["average_age"] == 15


def test_unavailable_metrics_stay_out_of_the_aggregations():
    """Sem Versão Usada, Tamanho/Idade são Indeterminados: fora da soma e da média."""
    dependencies = [
        {"package": "pandas", "origin": ORIGIN_PRODUCTION, "size": 1024, "age": 10},
        {
            "package": "ruff",
            "origin": ORIGIN_PRODUCTION,
            "size": UNKNOWN,
            "age": UNKNOWN,
        },
    ]

    summary = summarize_category(dependencies)

    assert summary["total_size"] == 1024
    assert summary["average_age"] == 10


def test_excluded_dependencies_are_counted_so_the_average_is_not_misleading():
    """Quantidade conta todas; a exclusão fica contabilizada, não escondida."""
    dependencies = [
        {"package": "pandas", "origin": ORIGIN_PRODUCTION, "size": 1024, "age": 10},
        {
            "package": "ruff",
            "origin": ORIGIN_PRODUCTION,
            "size": UNKNOWN,
            "age": UNKNOWN,
        },
    ]

    summary = summarize_category(dependencies)

    assert summary["count"] == 2
    assert summary["missing_size"] == 1
    assert summary["missing_age"] == 1


def test_empty_category_reports_unavailable_instead_of_dividing_by_zero():
    """Categoria vazia (ex.: nenhum Zumbi) é estado vazio, não erro."""
    summary = summarize_category([])

    assert summary["count"] == 0
    assert summary["total_size"] is None
    assert summary["average_age"] is None
    assert summary["missing_size"] == 0
    assert summary["missing_age"] == 0


def test_category_without_any_measured_metric_reports_unavailable():
    """Se ninguém tem Versão Usada resolvida, não há soma nem média a exibir."""
    dependencies = [
        {
            "package": "ruff",
            "origin": ORIGIN_PRODUCTION,
            "size": UNKNOWN,
            "age": UNKNOWN,
        }
    ]

    summary = summarize_category(dependencies)

    assert summary["count"] == 1
    assert summary["total_size"] is None
    assert summary["average_age"] is None
    assert summary["missing_size"] == 1


# ============ summarize_by_category (estratificação por Categoria) ============


def test_statistics_are_stratified_per_category():
    """Cada categoria do relatório ganha suas próprias estatísticas."""
    zombie = {"package": "altair", "origin": ORIGIN_PRODUCTION, "size": 512, "age": 400}
    healthy = {
        "package": "streamlit",
        "origin": ORIGIN_PRODUCTION,
        "size": 1024,
        "age": 10,
    }
    report = {
        "Todas as Dependências": [zombie, healthy],
        "Zumbis": [zombie],
        "Fantasmas": [],
    }

    summaries = summarize_by_category(report)

    assert summaries["Todas as Dependências"]["total_size"] == 1536
    assert summaries["Zumbis"]["total_size"] == 512
    assert summaries["Zumbis"]["average_age"] == 400
    assert summaries["Fantasmas"]["count"] == 0


def test_statistics_agree_with_the_category_tables():
    """A Quantidade de cada categoria bate com a lista que alimenta sua tabela."""
    report = {
        "Todas as Dependências": [{"package": "a"}, {"package": "b"}, {"package": "c"}],
        "Zumbis": [{"package": "a"}],
        "Desatualizadas": [{"package": "a"}, {"package": "b"}],
    }

    summaries = summarize_by_category(report)

    for category_label, dependencies in report.items():
        assert summaries[category_label]["count"] == len(dependencies)


def test_a_new_category_is_summarized_without_touching_the_aggregation():
    """Categoria nova entra na estratificação sozinha — nada de lista fixa."""
    report = {"Categoria Inédita": [{"package": "novo", "size": 2048, "age": 7}]}

    summaries = summarize_by_category(report)

    assert list(summaries) == ["Categoria Inédita"]
    assert summaries["Categoria Inédita"]["total_size"] == 2048


# ============ summary_metrics (as estatísticas descritas para exibição) ============


def test_summary_metrics_carry_the_value_not_the_sentence():
    """`core/` descreve a métrica; quem a redige é `utils/display.py` (ADR-0010).

    Enquanto isto devolvia "Tamanho: 2.0 MB" pronto, a caption chegava à tela em
    português sob `?lang=en` e não havia mais o que traduzir.
    """
    summary = summarize_category(
        [
            {"package": "a", "size": 1024 * 1024, "age": 10},
            {"package": "b", "size": 1024 * 1024, "age": 20},
        ]
    )

    metrics = summary_metrics(summary)

    assert [metric["metric"] for metric in metrics] == ["size", "age"]
    assert metrics[0]["value"] == 2 * 1024 * 1024  # bytes crus, não "2.0 MB"
    assert metrics[1]["value"] == 15  # dias, não "15 dias"


def test_summary_metrics_disclose_how_many_dependencies_were_left_out():
    """A média não engana: a contagem viaja junto do valor que ela afeta."""
    summary = summarize_category(
        [
            {"package": "a", "size": 1024, "age": 10},
            {"package": "b", "size": UNKNOWN, "age": UNKNOWN},
        ]
    )

    metrics = summary_metrics(summary)

    assert all(metric["missing"] == 1 for metric in metrics)
    assert all(metric["total"] == 2 for metric in metrics)


def test_summary_metrics_of_an_empty_category_have_no_value_and_nothing_excluded():
    """Categoria vazia não tem valor nem exclusão — não havia o que excluir."""
    metrics = summary_metrics(summarize_category([]))

    assert all(metric["value"] is None for metric in metrics)
    assert all(metric["missing"] == 0 for metric in metrics)


def test_summary_metrics_keep_the_average_unrounded():
    """Arredondar é decisão de exibição: a média sai como foi calculada."""
    summary = summarize_category(
        [{"package": "a", "age": 10}, {"package": "b", "age": 11}]
    )

    assert summary_metrics(summary)[1]["value"] == 10.5
