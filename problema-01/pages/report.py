"""
Módulo de exibição e exportação de relatórios de dependências.

Apresenta análise de dependências ao usuário através de métricas,
visualizações e tabelas, com opcionalidade de exportação em CSV/JSON.
"""

import streamlit as st
import plotly.express as px
from utils.sidebar import sidebar
from core.report.make_report import make_report
from core.report.export import export_to_csv, export_to_json
from utils.constants import MAPA_CORES_STATUS


CATEGORY_NAMES = {
    "all_dependencies": "Todas as Dependências",
    "zombies": "Zumbis",
    "ghosts": "Fantasmas",
    "outdated": "Desatualizadas",
}

CATEGORY_SESSION_KEYS = {
    "all_dependencies": "all_dependencies",
    "zombies": "zombies",
    "ghosts": "ghosts",
}


def _build_report_dictionary() -> dict[str, list]:
    """
    Constrói estrutura de relatório a partir do session_state.

    Agrupa dependências por categoria (todas, zumbis, fantasmas, desatualizadas)
    lendo do session_state populado pela página de loading.

    Returns:
        Dicionário com chaves de categoria e listas de dependências como valores.
        Exemplo: {
            "Todas as Dependências": [...],
            "Zumbis": [...],
            "Fantasmas": [...],
            "Desatualizadas": [...]
        }
    """
    all_deps = st.session_state.get("all_dependencies", [])
    zombies = st.session_state.get("zombies", [])
    ghosts = st.session_state.get("ghosts", [])

    outdated = [dep for dep in all_deps if dep.get("Status") == "Desatualizado"]

    return {
        CATEGORY_NAMES["all_dependencies"]: all_deps,
        CATEGORY_NAMES["zombies"]: zombies,
        CATEGORY_NAMES["ghosts"]: ghosts,
        CATEGORY_NAMES["outdated"]: outdated,
    }


def _calculate_healthy_dependencies(report_dict: dict[str, list]) -> int:
    """
    Calcula quantidade de dependências em bom estado.

    Dependências "saudáveis" = total - (zumbis + fantasmas + desatualizadas).
    Desacoplado de categorias hardcoded: opera sobre quaisquer chaves que não sejam
    a categoria "Todas as Dependências".

    Args:
        report_dict: Estrutura de relatório com categorias e listas.

    Returns:
        Quantidade de dependências sem problemas.
    """
    total = len(report_dict.get(CATEGORY_NAMES["all_dependencies"], []))

    for category_key, category_label in CATEGORY_NAMES.items():
        if category_key != "all_dependencies" and category_label in report_dict:
            total -= len(report_dict[category_label])

    return max(total, 0)


def _render_tabs_with_tables(report_dict: dict[str, list]) -> None:
    """
    Renderiza abas interativas com tabelas de dependências por categoria.

    Cada aba contém uma tabela formatada via make_report() associada
    a uma categoria de dependências.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    tabs = st.tabs(list(report_dict.keys()))
    for tab, (category_label, dependencies) in zip(tabs, report_dict.items()):
        with tab:
            st.table(make_report(dependencies))


def _render_metrics(report_dict: dict[str, list]) -> None:
    """
    Renderiza cartões de métrica para cada categoria de dependência.

    Exibe quantidade de itens em colunas paralelas, uma por categoria.
    Extensível: novas categorias são automaticamente incluídas sem alteração
    desta função.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    columns = st.columns(len(report_dict))
    for col, (category_label, dependencies) in zip(columns, report_dict.items()):
        col.metric(category_label, len(dependencies))


def _render_health_index(report_dict: dict[str, list]) -> None:
    """
    Renderiza índice de saúde do projeto como percentual e barra de progresso.

    Saúde = (dependências_saudáveis / total) * 100.
    Trata divisão por zero graciosamente.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    st.write("")
    total_dependencies = len(report_dict.get(CATEGORY_NAMES["all_dependencies"], []))

    if total_dependencies == 0:
        st.write("**Índice de Saúde do Projeto: N/A**")
        st.progress(0)
        return

    healthy_count = _calculate_healthy_dependencies(report_dict)
    health_percentage = int((healthy_count / total_dependencies) * 100)

    st.write(f"**Índice de Saúde do Projeto: {health_percentage}%**")
    st.progress(health_percentage / 100)


def _render_donut_chart(report_dict: dict[str, list]) -> None:
    """
    Renderiza gráfico de pizza (donut) com proporção de problemas por categoria.

    Agrupa dados de todas as categorias em estrutura adequada para Plotly.
    Extensível sem acoplamento: itera sobre CATEGORY_NAMES em lugar de hardcoding.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    chart_data = {
        "Status": ["OK ✅"],
        "Quantidade": [_calculate_healthy_dependencies(report_dict)],
    }

    for category_key, category_label in CATEGORY_NAMES.items():
        if category_key != "all_dependencies" and category_label in report_dict:
            chart_data["Status"].append(category_label)
            chart_data["Quantidade"].append(len(report_dict[category_label]))

    figure = px.pie(
        chart_data,
        values="Quantidade",
        names="Status",
        hole=0.4,
        color_discrete_map=MAPA_CORES_STATUS,
    )

    figure.update_layout(width=310, height=310, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(figure, use_container_width=False)


@st.dialog("Configurações do Relatório")
def _show_export_dialog(report_dict: dict[str, list]) -> None:
    """
    Exibe modal de diálogo para seleção e exportação de dados.

    Permite escolher quais categorias exportar e formato (CSV ou JSON).
    Gera download com nome padrão 'report_dp_auditor.{extensão}'.

    Args:
        report_dict: Estrutura de relatório com categorias e listas.
    """
    if not report_dict:
        st.warning("Não há dados para exportar.")
        return

    st.write("### 1. Selecione as categorias")
    selected_categories = []

    for category_label in report_dict.keys():
        if st.checkbox(
            category_label, value=True, key=f"export_category_{category_label}"
        ):
            selected_categories.append(category_label)

    st.divider()
    st.write("### 2. Formato do arquivo")
    file_format = st.radio("Escolha o formato:", ["CSV", "JSON"], horizontal=True)

    if not selected_categories:
        st.error("Selecione pelo menos uma categoria.")
        return

    data_to_export = []
    for category_label in selected_categories:
        data_to_export.extend(report_dict[category_label])

    if file_format == "CSV":
        exported_data = export_to_csv(data_to_export)
        mime_type = "text/csv"
        file_extension = "csv"
    else:
        exported_data = export_to_json(data_to_export)
        mime_type = "application/json"
        file_extension = "json"

    st.divider()

    st.download_button(
        label=f"Baixar Relatório .{file_extension} 📥",
        data=exported_data,
        file_name=f"report_dp_auditor.{file_extension}",
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
        st.warning("⚠️ Análise não realizada. Volte para a Home e inicie a auditoria.")
        st.stop()

    report_dict = _build_report_dictionary()

    if not report_dict.get(CATEGORY_NAMES["all_dependencies"]):
        st.warning("⚠️ Nenhuma dependência encontrada.")
        st.stop()

    col_metrics, col_chart = st.columns([3, 2], gap="large")

    with col_metrics:
        st.write("#### Principais Métricas")
        _render_metrics(report_dict)
        _render_health_index(report_dict)

    with col_chart:
        st.write("#### Proporção de Problemas Detectados")
        _render_donut_chart(report_dict)

    st.write("#### Tabelas por Categoria")
    _render_tabs_with_tables(report_dict)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Gerar Report 📋"):
            _show_export_dialog(report_dict)


sidebar()
st.title("📊 Relatório de Dependências")
_main()
