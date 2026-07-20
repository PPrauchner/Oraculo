"""
Estatísticas de Tamanho e Idade estratificadas por Categoria (US-06).

Responsabilidades:
- Agregar Quantidade, Tamanho somado e Idade média das dependências de uma categoria.
- Contar as dependências deixadas de fora por terem Tamanho/Idade indisponíveis.
- Formatar essas agregações para exibição, explicitando quantas ficaram de fora.
"""

from core.report.normalization import format_age, format_size
from utils.types import CategorySummary


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


def _with_exclusion_note(display: str, missing: int, total: int) -> str:
    """Anexa ao valor exibido quantas dependências ficaram fora dele.

    Uma Idade média calculada sobre metade dos pacotes, sem aviso, engana quem lê.
    A nota fica colada ao número que ela afeta, e some quando não há exclusão.

    Args:
        display: Valor já formatado.
        missing: Dependências sem a métrica.
        total: Dependências da categoria.

    Returns:
        O valor exibido, anotado com a exclusão quando houver.
    """
    if missing == 0:
        return display
    return f"{display} ({missing} de {total} sem dado)"


def format_summary_lines(summary: CategorySummary) -> list[str]:
    """Formata as estatísticas de uma categoria para exibição.

    Args:
        summary: Agregação produzida por `summarize_category`.

    Returns:
        Uma linha para o Tamanho somado e outra para a Idade média — "N/D" quando
        a categoria está vazia ou nenhuma dependência dela teve a métrica medida.
    """
    total = summary["count"]
    average_age = summary["average_age"]
    if average_age is None:
        readable_age = format_age(None)
    else:
        readable_age = format_age(round(average_age))

    return [
        _with_exclusion_note(
            f"Tamanho: {format_size(summary['total_size'])}",
            summary["missing_size"],
            total,
        ),
        _with_exclusion_note(
            f"Idade média: {readable_age}",
            summary["missing_age"],
            total,
        ),
    ]
