"""
Traduz o dado que `core/report/` devolve para o texto que o relatório mostra.

Responsabilidades:
- Formatar Tamanho e Idade crus na unidade e na língua da tela.
- Rotular Status e Origem a partir da identidade estável que `core/` devolve.
- Montar as linhas da tabela já com as colunas rotuladas.

É o mesmo papel que `utils/messages.py` cumpre para os códigos de erro de
`core/ingestion/`: `core/` devolve identidade e dado, e a redação, a unidade e a
língua são decisão de quem renderiza (ADR-0010). Antes disso `normalize` devolvia
"30 dias" e "(última versão)" prontos — com `?lang=en` a tabela respondia em
português, e não havia mais o que traduzir porque o dado já tinha virado frase.

Mora em `utils/` e não dentro de `pages/report.py` por dois motivos: a página
executa Streamlit já na importação, e nada que só ela possa importar é testável
como módulo; e o mesmo dado sai na tabela e nas métricas.

Este é o terceiro vocabulário do projeto, ao lado das chaves internas (snake_case)
e do cabeçalho do CSV (`CSV_HEADER`, Title Case fixo em inglês). São separados de
propósito: traduzir a tela não pode alcançar o arquivo exportado (ADR-0008).
"""

from typing import Callable

from utils.constants import (
    ORIGIN_DEVELOPMENT,
    ORIGIN_PRODUCTION,
    ORIGIN_UNAVAILABLE,
    STATUS_INVALID_VERSION,
    STATUS_OUTDATED,
    STATUS_UP_TO_DATE,
    UNKNOWN,
)
from utils.i18n import t
from utils.types import RawMetric, ReportRow, SummaryMetric

_BYTES_PER_KB = 1024
_BYTES_PER_MB = 1024 * 1024

# Chave interna da linha → chave de locale da coluna. A ordem é a ordem em que as
# colunas aparecem na tabela; a chave interna nunca chega à tela, porque ela é
# contrato do CSV e mudá-la por razão de tela reescreveria o arquivo (ADR-0008).
REPORT_COLUMNS = {
    "package": "report.column.package",
    "used_version": "report.column.used_version",
    "pypi_version": "report.column.pypi_version",
    "status": "report.column.status",
    "size": "report.column.size",
    "age": "report.column.age",
    "origin": "report.column.origin",
}

# O Indeterminado não aparece aqui: ele é a ausência, e `_value_label` já o resolve.
# Registrá-lo de novo criaria duas chaves de locale para o mesmo texto.
STATUS_KEYS = {
    STATUS_OUTDATED: "report.status.outdated",
    STATUS_UP_TO_DATE: "report.status.up_to_date",
    STATUS_INVALID_VERSION: "report.status.invalid_version",
}

ORIGIN_KEYS = {
    ORIGIN_PRODUCTION: "report.origin.production",
    ORIGIN_DEVELOPMENT: "report.origin.development",
}


def _value_label(value: str) -> str:
    """Rótulo das duas ausências; qualquer outro valor é dado do pacote.

    O `CONTEXT.md` separa Indeterminado ("o ORÁCULO não tem como saber") de Não
    Aplicável ("não existe por definição"), e a tela precisa manter a distinção:
    só a primeira diz ao usuário que adotar um Lock melhoraria o relatório dele.

    Args:
        value: Valor da linha, já como identidade estável.

    Returns:
        O rótulo traduzido quando o valor é uma das ausências; o próprio valor
        quando é dado do pacote — nome e número não se traduzem.
    """
    if value == UNKNOWN:
        return t("report.value.unknown")
    if value == ORIGIN_UNAVAILABLE:
        return t("report.value.not_applicable")
    return value


def format_size(size: RawMetric) -> str:
    """Formata o Tamanho cru (bytes) na unidade legível.

    Args:
        size: Bytes da Versão Usada, ou o Indeterminado quando não medido.

    Returns:
        "X.Y MB" a partir de 1 MB, "X.Y KB" abaixo disso — nunca 0 para o caso não
        medido. KB e MB são símbolo de unidade, não palavra: não mudam com a língua.
    """
    if not isinstance(size, (int, float)):
        return _value_label(size)

    if size >= _BYTES_PER_MB:
        return f"{size / _BYTES_PER_MB:.1f} MB"
    return f"{size / _BYTES_PER_KB:.1f} KB"


def format_age(age: RawMetric) -> str:
    """Formata a Idade crua (dias inteiros) no texto da língua da tela.

    Args:
        age: Dias desde a publicação da Versão Usada, ou o Indeterminado.

    Returns:
        A contagem de dias redigida pelo locale — o plural é decisão de língua e
        por isso mora lá, não aqui.
    """
    if not isinstance(age, (int, float)):
        return _value_label(age)

    days = int(age)
    key = "report.age.day" if days == 1 else "report.age.days"
    return t(key).format(days=days)


def status_label(status: str) -> str:
    """Rótulo de um Status na língua da tela.

    Args:
        status: Identidade estável, como `core/analysis/` a devolve.

    Returns:
        O texto a exibir. A identidade segue em inglês porque é comparada para
        montar a coluna Outdated do CSV; o que muda com a língua é só o texto.
    """
    key = STATUS_KEYS.get(status)
    return t(key) if key else _value_label(status)


def origin_label(origin: str) -> str:
    """Rótulo de uma Origem na língua da tela.

    Args:
        origin: Identidade estável (Produção, Desenvolvimento) ou o Não Aplicável
            de um Fantasma, que não vem de Declaração nenhuma.

    Returns:
        O texto a exibir.
    """
    key = ORIGIN_KEYS.get(origin)
    return t(key) if key else _value_label(origin)


def _metric_text(
    raw: RawMetric, from_latest: bool, formatter: Callable[[RawMetric], str]
) -> str:
    """Formata Tamanho/Idade e explicita quando a referência é a versão mais recente.

    Args:
        raw: Valor cru da métrica.
        from_latest: Se a métrica se refere à versão mais recente do PyPI, e não à
            Versão Usada — o caso do Fantasma, que não tem Declaração.
        formatter: `format_size` ou `format_age`.

    Returns:
        O texto da célula, anotado quando há número e ele descreve outra versão.
        Sem número não há o que anotar: a nota diz de que versão o número é.
    """
    text = formatter(raw)
    if from_latest and isinstance(raw, (int, float)):
        return f"{text} ({t('report.metric.latest_version')})"
    return text


def _cells(row: ReportRow) -> dict[str, str]:
    """Traduz cada campo de uma linha para o texto da sua célula."""
    from_latest = row["metrics_from_latest"]

    return {
        "package": row["package"],
        "used_version": _value_label(row["used_version"]),
        "pypi_version": _value_label(row["pypi_version"]),
        "status": status_label(row["status"]),
        "size": _metric_text(row["size"], from_latest, format_size),
        "age": _metric_text(row["age"], from_latest, format_age),
        "origin": origin_label(row["origin"]),
    }


def display_rows(rows: list[ReportRow]) -> list[dict[str, str]]:
    """Monta a tabela do relatório na língua da tela.

    Args:
        rows: Linhas como `normalize` as devolve — dado cru e identidade estável.

    Returns:
        Uma linha por dependência, chaveada pelo rótulo da coluna: é a chave que o
        Streamlit usa como cabeçalho da tabela. `metrics_from_latest` não vira
        coluna — ele anota o Tamanho e a Idade, não é dado a exibir por si.
    """
    table = []

    for row in rows:
        cells = _cells(row)
        table.append({t(key): cells[field] for field, key in REPORT_COLUMNS.items()})

    return table


# Identidade da métrica → rótulo da caption e formatador do seu valor. O rótulo
# nomeia a agregação, e não a coluna: é o Tamanho *somado* e a Idade *média* da
# categoria, e chamá-los como a tabela ao lado confundiria as duas leituras.
SUMMARY_METRICS: dict[str, tuple[str, Callable[[RawMetric], str]]] = {
    "size": ("report.summary.total_size", format_size),
    "age": ("report.summary.average_age", format_age),
}


def format_summary_metric(metric: SummaryMetric) -> str:
    """Redige a caption de uma estatística de categoria, na língua da tela.

    Args:
        metric: Identidade e dados como `summary_metrics` os devolve.

    Returns:
        A linha a exibir, anotada com quantas dependências ficaram fora da
        agregação. A nota some quando não houve exclusão — não havia o que excluir.
    """
    key, formatter = SUMMARY_METRICS[metric["metric"]]
    value = metric["value"]

    # A Idade média sai fracionária e a tela conta dias inteiros; o Tamanho já é
    # inteiro, então o mesmo arredondamento serve aos dois sem ramificar.
    raw: RawMetric = UNKNOWN if value is None else round(value)
    line = f"{t(key)}: {formatter(raw)}"

    if metric["missing"]:
        note = t("report.summary.missing").format(
            missing=metric["missing"], total=metric["total"]
        )
        return f"{line} {note}"

    return line
