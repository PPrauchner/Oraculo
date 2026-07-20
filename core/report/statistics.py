"""
Estatísticas de Tamanho e Idade estratificadas por Categoria (US-06).

Responsabilidades:
- Agregar Quantidade, Tamanho somado e Idade média das dependências de uma categoria.
- Contar as dependências deixadas de fora por terem Tamanho/Idade indisponíveis.
- Descrever essas agregações para exibição, explicitando quantas ficaram de fora.

Descrever, e não redigir: a caption sai daqui como identidade e dado, e o texto
nasce em `utils/display.py`, na língua da tela (ADR-0010).
"""

from utils.types import CategorySummary, SummaryMetric


def _available(dependencies: list[dict], metric: str) -> list[float]:
    """Valores numéricos de uma métrica, descartando os indisponíveis.

    Sem Versão Usada resolvida, Tamanho e Idade saem como o sentinela de
    indisponibilidade (ADR-0002/ADR-0004). Somar ou mediar esse sentinela como 0
    inventaria um número que o PyPI não deu.

    Args:
        dependencies: Dependências da categoria.
        metric: "size" ou "age".

    Returns:
        Somente os valores efetivamente medidos.
    """
    values = [dep.get(metric) for dep in dependencies]
    return [value for value in values if isinstance(value, (int, float))]


def summarize_category(dependencies: list[dict]) -> CategorySummary:
    """Agrega Quantidade, Tamanho e Idade das dependências de uma categoria.

    Args:
        dependencies: Dependências da categoria.

    Returns:
        `count` (todas as dependências da categoria), `total_size` e `average_age`
        (só as efetivamente medidas, ou ``None`` quando nenhuma foi), e
        `missing_size`/`missing_age` com quantas ficaram de fora de cada agregação.
    """
    sizes = _available(dependencies, "size")
    ages = _available(dependencies, "age")

    return {
        "count": len(dependencies),
        "total_size": sum(sizes) if sizes else None,
        "average_age": sum(ages) / len(ages) if ages else None,
        "missing_size": len(dependencies) - len(sizes),
        "missing_age": len(dependencies) - len(ages),
    }


def summarize_by_category(report: dict[str, list[dict]]) -> dict[str, CategorySummary]:
    """Estratifica as estatísticas por Categoria (US-06).

    Percorre as categorias que o relatório trouxer, sem lista fixa: acrescentar
    uma categoria nova ao relatório basta para que ela apareça nas estatísticas.

    Args:
        report: Categoria (rótulo) para as dependências que a compõem.

    Returns:
        Uma agregação de `summarize_category` por categoria, na mesma ordem.
    """
    return {
        category_label: summarize_category(dependencies)
        for category_label, dependencies in report.items()
    }


def summary_metrics(summary: CategorySummary) -> list[SummaryMetric]:
    """Descreve as estatísticas de uma categoria para quem for exibi-las.

    Devolve a identidade da métrica e os dados que a descrevem, não a frase
    (ADR-0010). A anterior — "Tamanho: 1.2 MB (1 de 2 sem dado)" — nascia pronta e
    em português aqui dentro, e sob `?lang=en` chegava à tela sem nada a traduzir.

    A contagem de quantas ficaram de fora viaja junto do valor de propósito: uma
    Idade média calculada sobre metade dos pacotes, sem aviso, engana quem lê.

    Args:
        summary: Agregação produzida por `summarize_category`.

    Returns:
        O Tamanho somado e a Idade média, nesta ordem, cada um com quantas
        dependências ficaram fora da agregação e de quantas.
    """
    total = summary["count"]

    return [
        {
            "metric": "size",
            "value": summary["total_size"],
            "missing": summary["missing_size"],
            "total": total,
        },
        {
            "metric": "age",
            "value": summary["average_age"],
            "missing": summary["missing_age"],
            "total": total,
        },
    ]
