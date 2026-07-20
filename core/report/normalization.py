"""
Módulo responsável pela construção do relatório final.

Organiza os dados provenientes da análise em uma estrutura adequada
para visualização e exportação (ex: DataFrame).

Entrada:
- Lista com todas as dependências
- Resultados das análises (zumbis, fantasmas, desatualizados)

Saída:
- Estrutura de dados organizada (ex: Dicionário)
"""

from typing import Callable

from core.analysis.ghost_analizer import is_ghost
from utils.constants import (
    CATEGORY_GHOST,
    CATEGORY_HEALTHY,
    CATEGORY_ZOMBIE,
    ORIGIN_UNAVAILABLE,
    OUTDATED_NO,
    OUTDATED_YES,
    VERSION_UNAVAILABLE,
)
from utils.types import Dependency, ExportRow, ReportRow

_OUTDATED_STATUS = "Desatualizado"

_BYTES_PER_KB = 1024
_BYTES_PER_MB = 1024 * 1024
_LATEST_VERSION_NOTE = "última versão"


def format_size(size: object) -> str:
    """Formata o Tamanho cru (bytes) em unidade legível (KB/MB).

    Args:
        size: Bytes inteiros da Versão Usada, ou o sentinela de indisponibilidade.

    Returns:
        "X.Y MB" a partir de 1 MB, "X.Y KB" abaixo disso, ou "N/D" quando
        indisponível — nunca 0 para o caso indisponível.
    """
    if not isinstance(size, (int, float)):
        return VERSION_UNAVAILABLE

    if size >= _BYTES_PER_MB:
        return f"{size / _BYTES_PER_MB:.1f} MB"
    return f"{size / _BYTES_PER_KB:.1f} KB"


def format_age(age: object) -> str:
    """Formata a Idade crua (dias inteiros) em texto legível.

    Args:
        age: Dias inteiros desde a publicação da Versão Usada, ou o sentinela de
            indisponibilidade.

    Returns:
        "N dia(s)", ou "N/D" quando indisponível.
    """
    if not isinstance(age, (int, float)):
        return VERSION_UNAVAILABLE

    days = int(age)
    return f"{days} dia" if days == 1 else f"{days} dias"


def _display_metric(
    raw: object, is_fantasma: bool, formatter: Callable[[object], str]
) -> str:
    """Formata Tamanho/Idade e, para Fantasma, explicita que é da versão mais recente.

    Args:
        raw: Valor cru da métrica.
        is_fantasma: Se a dependência é Fantasma (sem Declaração/Versão Usada), caso
            em que a referência é a versão mais recente do PyPI.
        formatter: `format_size` ou `format_age`.

    Returns:
        Texto legível, anotado com "(última versão)" quando Fantasma e disponível.
    """
    display = formatter(raw)
    if is_fantasma and display != VERSION_UNAVAILABLE:
        display = f"{display} ({_LATEST_VERSION_NOTE})"
    return display


def normalize(list_analyzed: list[Dependency]) -> list[ReportRow]:
    """
    Constrói um Dicionário consolidando os resultados das análises.

    Args:
        list_analyzed: Dependências com seus resultados de análise.

    Returns:
        As linhas do relatório final, com Tamanho e Idade já formatados.
    """

    rows: list[ReportRow] = []

    for dep in list_analyzed:
        # Fantasma não tem Declaração, logo não tem Origem (CONTEXT.md): seu
        # Tamanho/Idade referem-se à versão mais recente, e a tabela o explicita.
        is_fantasma = is_ghost(dep)
        rows.append(
            {
                "package": dep.get("package", "N/A"),
                "used_version": dep.get("used_version", "N/A"),
                "pypi_version": dep.get("pypi_version", "N/A"),
                "status": dep.get("status", "Desconhecido"),
                "size": _display_metric(
                    dep.get("size", VERSION_UNAVAILABLE), is_fantasma, format_size
                ),
                "Idade": _display_metric(
                    dep.get("Idade", VERSION_UNAVAILABLE), is_fantasma, format_age
                ),
                "origin": dep.get("origin", "N/A"),
            }
        )

    if not rows:
        empty: ReportRow = {
            "package": "N/A",
            "used_version": "N/A",
            "pypi_version": "N/A",
            "status": "N/A",
            "size": "N/A",
            "Idade": "N/A",
            "origin": "N/A",
        }
        return [empty]
    return rows


def build_export_rows(
    dependencies: list[Dependency],
    zombies: list[Dependency],
    ghosts: list[Dependency],
    project_name: str,
    analysis_date: str,
) -> list[ExportRow]:
    """Monta as linhas da exportação (US-06/US-07), uma por dependência.

    O esquema acrescenta um eixo temporal (Data da Análise) e de identidade
    (Projeto), e estratifica por Categoria (Zumbi, Fantasma, Saudável). Desatualizada
    é coluna própria — uma dependência pode ser Zumbi *e* Desatualizada ao mesmo
    tempo, o que um único campo Categoria perderia.

    Tamanho e Idade saem crus (bytes e dias inteiros) ou como o sentinela de
    indisponibilidade, nunca formatados nem 0: o CSV é para diffing/concatenação ao
    longo do tempo, não para leitura humana direta (essa é a `normalize`).

    Args:
        dependencies: Todas as dependências auditadas (Declaradas + Fantasmas),
            já deduplicadas.
        zombies: Dependências Zumbi identificadas pela análise.
        ghosts: Dependências Fantasma identificadas pela análise.
        project_name: Identificador do Projeto-Alvo (mesmo valor em toda linha).
        analysis_date: Data da Análise (mesmo valor em toda linha da exportação).

    Returns:
        Uma linha por dependência, na ordem das colunas do esquema.
    """
    zombie_names = {dep["package"] for dep in zombies}
    ghost_names = {dep["package"] for dep in ghosts}

    rows: list[ExportRow] = []
    for dep in dependencies:
        package = dep.get("package", "N/A")

        if package in zombie_names:
            category = CATEGORY_ZOMBIE
        elif package in ghost_names:
            category = CATEGORY_GHOST
        else:
            category = CATEGORY_HEALTHY

        outdated = OUTDATED_YES if dep.get("status") == _OUTDATED_STATUS else OUTDATED_NO

        rows.append(
            {
                "Data da Análise": analysis_date,
                "Projeto": project_name,
                "package": package,
                "Categoria": category,
                # Fantasma não tem Declaração, logo não tem Origem (CONTEXT.md).
                "origin": dep.get("origin", ORIGIN_UNAVAILABLE),
                "used_version": dep.get("used_version", "N/A"),
                "pypi_version": dep.get("pypi_version", "N/A"),
                "Desatualizada": outdated,
                "size": dep.get("size", VERSION_UNAVAILABLE),
                "Idade": dep.get("Idade", VERSION_UNAVAILABLE),
            }
        )

    return rows


def filter_export_rows(
    rows: list[ExportRow],
    categories: set[str],
    include_outdated: bool,
) -> list[ExportRow]:
    """Seleciona as linhas de exportação pedidas, sem repetir nenhuma dependência.

    Desatualizada não é Categoria, então entra como critério à parte. Uma linha que
    satisfaz os dois critérios (ex.: Zumbi *e* Desatualizada) sai uma única vez —
    filtrar preserva a regra de uma linha por dependência.

    Args:
        rows: Linhas produzidas por `build_export_rows`.
        categories: Categorias selecionadas (Zumbi, Fantasma, Saudável).
        include_outdated: Se as Dependências Desatualizadas também entram.

    Returns:
        As linhas selecionadas, na ordem original.
    """
    return [
        row
        for row in rows
        if row["Categoria"] in categories
        or (include_outdated and row["Desatualizada"] == OUTDATED_YES)
    ]
