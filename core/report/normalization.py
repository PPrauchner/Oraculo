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

from core.analysis.ghost_analizer import is_ghost
from utils.constants import (
    CATEGORY_GHOST,
    CATEGORY_HEALTHY,
    CATEGORY_ZOMBIE,
    ORIGIN_UNAVAILABLE,
    OUTDATED_NO,
    OUTDATED_YES,
    STATUS_OUTDATED,
    STATUS_UNKNOWN,
    UNKNOWN,
)
from utils.types import Dependency, ExportRow, ReportRow


def normalize(list_analyzed: list[Dependency]) -> list[ReportRow]:
    """Seleciona, de cada Dependência, o que a tabela do relatório exibe.

    Devolve dado e identidade, nunca texto pronto: Tamanho em bytes, Idade em dias,
    Status como identidade estável. Quem escolhe unidade, redação e língua é
    `utils/display.py` (ADR-0010) — enquanto esta função devolvia "30 dias", a
    tabela respondia em português sob `?lang=en`.

    Args:
        list_analyzed: Dependências com seus resultados de análise.

    Returns:
        Uma linha por dependência, ou uma linha de Não Aplicável quando não há
        nenhuma — a tabela precisa de forma mesmo vazia.
    """

    rows: list[ReportRow] = []

    for dep in list_analyzed:
        rows.append(
            {
                "package": dep.get("package", ORIGIN_UNAVAILABLE),
                "used_version": dep.get("used_version", ORIGIN_UNAVAILABLE),
                "pypi_version": dep.get("pypi_version", ORIGIN_UNAVAILABLE),
                "status": dep.get("status", STATUS_UNKNOWN),
                "size": dep.get("size", UNKNOWN),
                "age": dep.get("age", UNKNOWN),
                "origin": dep.get("origin", ORIGIN_UNAVAILABLE),
                # Fantasma não tem Declaração, logo não tem Versão Usada (CONTEXT.md):
                # seu Tamanho/Idade referem-se à versão mais recente do PyPI, e a
                # tabela precisa poder dizer isso.
                "metrics_from_latest": is_ghost(dep),
            }
        )

    if not rows:
        empty: ReportRow = {
            "package": ORIGIN_UNAVAILABLE,
            "used_version": ORIGIN_UNAVAILABLE,
            "pypi_version": ORIGIN_UNAVAILABLE,
            "status": ORIGIN_UNAVAILABLE,
            "size": ORIGIN_UNAVAILABLE,
            "age": ORIGIN_UNAVAILABLE,
            "origin": ORIGIN_UNAVAILABLE,
            "metrics_from_latest": False,
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

        outdated = OUTDATED_YES if dep.get("status") == STATUS_OUTDATED else OUTDATED_NO

        rows.append(
            {
                "analysis_date": analysis_date,
                "project": project_name,
                "package": package,
                "category": category,
                # Fantasma não tem Declaração, logo não tem Origem (CONTEXT.md).
                "origin": dep.get("origin", ORIGIN_UNAVAILABLE),
                "used_version": dep.get("used_version", "N/A"),
                "pypi_version": dep.get("pypi_version", "N/A"),
                "outdated": outdated,
                "size": dep.get("size", UNKNOWN),
                "age": dep.get("age", UNKNOWN),
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
        if row["category"] in categories
        or (include_outdated and row["outdated"] == OUTDATED_YES)
    ]
