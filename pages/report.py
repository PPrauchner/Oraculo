"""
Módulo de exibição e exportação de relatórios de dependências.

Apresenta análise de dependências ao usuário através de métricas,
visualizações e tabelas, com opcionalidade de exportação em CSV/JSON.
"""

import streamlit as st
import plotly.express as px
from utils.sidebar import sidebar
from core.report.normalization import normalize, build_export_rows, filter_export_rows
from core.report.statistics import format_summary_lines, summarize_by_category
from core.report.export import export_to_csv, export_to_json
from utils.constants import (
    CATEGORY_ZOMBIE,
    CATEGORY_GHOST,
)
from utils.i18n import t
from utils.theme import status_colors


# Identidade estável de cada categoria do relatório. É ela que serve de chave do
# `report_dict`, de chave dos checkboxes em `session_state` e de chave do mapa de
# cores do donut — nunca o rótulo, que muda com a língua. Traduzir a chave faria a
# troca de idioma desmarcar as caixas e derrubar as cores do gráfico (ADR-0009).
REPORT_ALL = "all_dependencies"
REPORT_ZOMBIES = "zombies"
REPORT_GHOSTS = "ghosts"
REPORT_OUTDATED = "outdated"

# Saudável não é aba nem métrica — é a fatia do donut que sobra quando nenhuma
# análise apontou problema —, por isso fica fora de `REPORT_CATEGORIES`.
REPORT_HEALTHY = "healthy"

# As categorias do relatório, na ordem em que aparecem nas abas e nas métricas.
REPORT_CATEGORIES = (REPORT_ALL, REPORT_ZOMBIES, REPORT_GHOSTS, REPORT_OUTDATED)

# Ponte entre a categoria escolhida no diálogo e a Categoria da linha exportada.
# "Desatualizadas" não aparece aqui: é coluna própria, não Categoria. O valor
# exportado é fixo em inglês e não acompanha o seletor de língua (ADR-0008).
EXPORT_CATEGORIES = {
    REPORT_ZOMBIES: CATEGORY_ZOMBIE,
    REPORT_GHOSTS: CATEGORY_GHOST,
}

CATEGORY_SESSION_KEYS = {
    "all_dependencies": "all_dependencies",
    "zombies": "zombies",
    "ghosts": "ghosts",
}


def _category_label(category: str) -> str:
    """Rótulo de uma categoria do relatório na língua da tela.

    Args:
        category: Identidade estável da categoria (`REPORT_*`), ou "healthy" para a
            fatia das dependências sem problema apontado.

    Returns:
        O texto a exibir, resolvido na renderização — nunca guardado.
    """
    return t(f"report.category.{category}")


def _build_report_dictionary() -> dict[str, list]:
    """
    Constrói estrutura de relatório a partir do session_state.

    Agrupa dependências por categoria (todas, zumbis, fantasmas, desatualizadas)
    lendo do session_state populado pela página de loading.

    Returns:
        Dicionário da identidade estável de cada categoria (`REPORT_*`) para as
        dependências que a compõem. A chave não é o rótulo: o rótulo só nasce na
        renderização, na língua da tela.
    """
    all_deps = st.session_state.get("all_dependencies", [])
    zombies = st.session_state.get("zombies", [])
    ghosts = st.session_state.get("ghosts", [])

    outdated = [dep for dep in all_deps if dep.get("status") == "Desatualizado"]

    return {
        REPORT_ALL: all_deps,
        REPORT_ZOMBIES: zombies,
        REPORT_GHOSTS: ghosts,
        REPORT_OUTDATED: outdated,
    }


def _calculate_healthy_dependencies(report_dict: dict[str, list[dict]]) -> int:
    all_deps = report_dict.get(REPORT_ALL, [])

    # Criamos um set apenas com os IDs/Nomes das dependências problemáticas
    problematic_ids = set()

    for category in REPORT_CATEGORIES:
        if category != REPORT_ALL and category in report_dict:
            for dep in report_dict[category]:
                # Guardamos apenas o identificador único (ex: o nome da lib)
                problematic_ids.add(dep["package"])

    # Contamos quantas deps do total NÃO estão no set de IDs problemáticos
    healthy_count = 0
    for dep in all_deps:
        if dep["package"] not in problematic_ids:
            healthy_count += 1

    return healthy_count


def _render_tabs_with_tables(report_dict: dict[str, list]) -> None:
    """
    Renderiza abas interativas com tabelas de dependências por categoria.

    Cada aba contém uma tabela formatada via normalize() associada
    a uma categoria de dependências.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    tabs = st.tabs([_category_label(category) for category in report_dict])
    for tab, dependencies in zip(tabs, report_dict.values()):
        with tab:
            st.table(normalize(dependencies))


def _render_metrics(report_dict: dict[str, list]) -> None:
    """
    Renderiza cartões de métrica para cada categoria de dependência.

    Exibe, em colunas paralelas (uma por categoria), a quantidade de dependências,
    o Tamanho somado e a Idade média (US-06) — anotando quantas ficaram de fora das
    agregações por terem Tamanho/Idade indisponíveis. Extensível: novas categorias
    são automaticamente incluídas sem alteração desta função.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    summaries = summarize_by_category(report_dict)
    columns = st.columns(len(summaries))
    for col, (category, summary) in zip(columns, summaries.items()):
        col.metric(_category_label(category), summary["Quantidade"])
        for line in format_summary_lines(summary):
            col.caption(line)


def _render_health_index(report_dict: dict[str, list]) -> None:
    """
    Renderiza índice de saúde do projeto como percentual e barra de progresso.

    Saúde = (dependências_saudáveis / total) * 100.
    Trata divisão por zero graciosamente.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    st.write("")
    total_dependencies = len(report_dict.get(REPORT_ALL, []))

    if total_dependencies == 0:
        st.write(f"**{t('report.health_index')}: {t('report.health_index.unavailable')}**")
        st.progress(0)
        return

    healthy_count = _calculate_healthy_dependencies(report_dict)
    health_percentage = int((healthy_count / total_dependencies) * 100)

    st.write(f"**{t('report.health_index')}: {health_percentage}%**")
    st.progress(health_percentage / 100)


def _render_donut_chart(report_dict: dict[str, list]) -> None:
    """
    Renderiza gráfico de pizza (donut) com proporção de problemas por categoria.

    Agrupa dados de todas as categorias em estrutura adequada para Plotly.
    Extensível sem acoplamento: itera sobre REPORT_CATEGORIES em lugar de hardcoding.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    chart_data = {
        "Status": [_category_label(REPORT_HEALTHY)],
        "Quantidade": [_calculate_healthy_dependencies(report_dict)],
    }

    for category in REPORT_CATEGORIES:
        if category != REPORT_ALL and category in report_dict:
            chart_data["Status"].append(_category_label(category))
            chart_data["Quantidade"].append(len(report_dict[category]))

    figure = px.pie(
        chart_data,
        values="Quantidade",
        names="Status",
        hole=0.4,
        # A cor de cada Categoria vem da paleta do tema, então a fatia acompanha o
        # modo claro/escuro em vez de carregar um hex próprio. O mapa é rechaveado
        # no rótulo traduzido porque é por ele que o Plotly casa a fatia com a cor —
        # a paleta continua indexada pela identidade estável da categoria.
        color_discrete_map={
            _category_label(category): color
            for category, color in status_colors().items()
        },
    )

    figure.update_layout(width=310, height=310, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(figure, use_container_width=False)


@st.dialog(t("report.export.title"))
def _show_export_dialog(report_dict: dict[str, list]) -> None:
    """
    Exibe modal de diálogo para seleção e exportação de dados.
    """
    if not report_dict:
        st.warning(t("report.export.no_data"))
        return

    others = [category for category in report_dict if category != REPORT_ALL]

    def on_change_all():
        """Sincroniza todas as categorias com o checkbox 'Todas'."""
        new_val = st.session_state[f"cb_{REPORT_ALL}"]
        for category in others:
            st.session_state[f"cb_{category}"] = new_val

    def on_change_individual():
        """Sincroniza o checkbox 'Todas' com as categorias individuais."""
        all_checked = all(
            st.session_state.get(f"cb_{category}", False) for category in others
        )
        st.session_state[f"cb_{REPORT_ALL}"] = all_checked

    st.write(f"### {t('report.export.select_categories')}")

    # A chave do checkbox é a identidade da categoria, não o rótulo: com o rótulo,
    # trocar de língua criaria uma chave nova em `session_state` e a caixa marcada
    # voltaria ao padrão sem que ninguém a tivesse desmarcado.
    st.checkbox(
        _category_label(REPORT_ALL),
        key=f"cb_{REPORT_ALL}",
        on_change=on_change_all,
        value=st.session_state.get(f"cb_{REPORT_ALL}", True),  # Valor padrão inicial
    )

    cols = st.columns(len(others))
    for i, category in enumerate(others):
        cols[i].checkbox(
            _category_label(category),
            key=f"cb_{category}",
            on_change=on_change_individual,
            value=st.session_state.get(f"cb_{category}", True),  # Valor padrão inicial
        )

    st.divider()

    st.write(f"### {t('report.export.file_format')}")
    file_format = st.radio(
        t("report.export.format_label"), ["CSV", "JSON"], horizontal=True
    )

    selected = [
        category
        for category in report_dict
        if st.session_state.get(f"cb_{category}")
    ]

    if not selected:
        st.error(t("report.export.no_category"))
        return

    # As linhas nascem do conjunto auditado inteiro — já deduplicado e enriquecido
    # com o PyPI — e a seleção apenas filtra. Assim uma dependência que cai em duas
    # categorias (ex.: Zumbi e Desatualizada) continua exportando uma única linha.
    export_rows = build_export_rows(
        report_dict[REPORT_ALL],
        zombies=report_dict[REPORT_ZOMBIES],
        ghosts=report_dict[REPORT_GHOSTS],
        project_name=st.session_state.get("project_name", "N/A"),
        analysis_date=st.session_state.get("analysis_date", "N/A"),
    )

    if st.session_state.get(f"cb_{REPORT_ALL}"):
        final_list = export_rows
    else:
        selected_categories = {
            EXPORT_CATEGORIES[category]
            for category in selected
            if category in EXPORT_CATEGORIES
        }
        include_outdated = REPORT_OUTDATED in selected
        final_list = filter_export_rows(
            export_rows, selected_categories, include_outdated
        )

    if file_format == "CSV":
        exported_data = export_to_csv(final_list)
        mime_type, file_ext = "text/csv", "csv"
    else:
        exported_data = export_to_json(final_list)
        mime_type, file_ext = "application/json", "json"

    st.divider()

    st.download_button(
        label=t("report.export.download").format(
            count=len(final_list), extension=file_ext
        ),
        data=exported_data,
        file_name=f"report_oraculo.{file_ext}",
        mime=mime_type,
        use_container_width=True,
    )


def _main() -> None:
    """
    Orquestra renderização completa da página de relatório.

    Verifica pré-condições (análise completa), constrói estrutura de dados,
    e renderiza componentes (métricas, gráficos, tabelas, exportação).
    """
    if not st.session_state.get("analysis_complete", False):
        st.warning(t("report.warning.not_run"))
        st.stop()

    report_dict = _build_report_dictionary()

    if not report_dict.get(REPORT_ALL):
        st.warning(t("report.warning.no_dependency"))
        st.stop()

    col_metrics, col_chart = st.columns([3, 2], gap="large")

    with col_metrics:
        st.write(f"#### {t('report.metrics.header')}")
        _render_metrics(report_dict)
        _render_health_index(report_dict)

    with col_chart:
        st.write(f"#### {t('report.chart.header')}")
        _render_donut_chart(report_dict)

    st.write(f"#### {t('report.tables.header')}")
    _render_tabs_with_tables(report_dict)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button(t("report.generate")):
            _show_export_dialog(report_dict)


sidebar()
st.title(t("report.title"))
_main()
