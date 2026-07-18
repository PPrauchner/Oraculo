"""
Módulo de exibição e exportação de relatórios de dependências.

Apresenta análise de dependências ao usuário através de métricas,
visualizações e tabelas, com opcionalidade de exportação em CSV/JSON.
"""

import streamlit as st
import plotly.express as px
from utils.sidebar import sidebar
from core.report.normalization import normalize, build_export_rows, filter_export_rows
from core.report.export import export_to_csv, export_to_json
from utils.constants import (
    MAPA_CORES_STATUS,
    CATEGORY_ZOMBIE,
    CATEGORY_GHOST,
)


CATEGORY_NAMES = {
    "all_dependencies": "Todas as Dependências",
    "zombies": "Zumbis",
    "ghosts": "Fantasmas",
    "outdated": "Desatualizadas",
}

# Ponte entre o rótulo do diálogo de exportação e a Categoria da linha exportada.
# "Desatualizadas" não aparece aqui: é coluna própria, não Categoria.
EXPORT_CATEGORIES = {
    CATEGORY_NAMES["zombies"]: CATEGORY_ZOMBIE,
    CATEGORY_NAMES["ghosts"]: CATEGORY_GHOST,
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


def _calculate_healthy_dependencies(report_dict: dict[str, list[dict]]) -> int:
    all_deps = report_dict.get(CATEGORY_NAMES["all_dependencies"], [])

    # Criamos um set apenas com os IDs/Nomes das dependências problemáticas
    problematic_ids = set()

    for category_key, category_label in CATEGORY_NAMES.items():
        if category_key != "all_dependencies" and category_label in report_dict:
            for dep in report_dict[category_label]:
                # Guardamos apenas o identificador único (ex: o nome da lib)
                problematic_ids.add(dep["Pacote"])

    # Contamos quantas deps do total NÃO estão no set de IDs problemáticos
    healthy_count = 0
    for dep in all_deps:
        if dep["Pacote"] not in problematic_ids:
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
    tabs = st.tabs(list(report_dict.keys()))
    for tab, (category_label, dependencies) in zip(tabs, report_dict.items()):
        with tab:
            st.table(normalize(dependencies))


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
    """
    if not report_dict:
        st.warning("Não há dados para exportar.")
        return

    ALL_LABEL = CATEGORY_NAMES["all_dependencies"]
    other_labels = [label for label in report_dict.keys() if label != ALL_LABEL]

    def on_change_all():
        """Sincroniza todas as categorias com o checkbox 'Todas'."""
        new_val = st.session_state[f"cb_{ALL_LABEL}"]
        for label in other_labels:
            st.session_state[f"cb_{label}"] = new_val

    def on_change_individual():
        """Sincroniza o checkbox 'Todas' com as categorias individuais."""
        all_checked = all(
            st.session_state.get(f"cb_{label}", False) for label in other_labels
        )
        st.session_state[f"cb_{ALL_LABEL}"] = all_checked

    st.write("### 1. Selecione as categorias")

    st.checkbox(
        ALL_LABEL,
        key=f"cb_{ALL_LABEL}",
        on_change=on_change_all,
        value=st.session_state.get(f"cb_{ALL_LABEL}", True),  # Valor padrão inicial
    )

    cols = st.columns(len(other_labels))
    for i, label in enumerate(other_labels):
        cols[i].checkbox(
            label,
            key=f"cb_{label}",
            on_change=on_change_individual,
            value=st.session_state.get(f"cb_{label}", True),  # Valor padrão inicial
        )

    st.divider()

    st.write("### 2. Formato do arquivo")
    file_format = st.radio("Escolha o formato:", ["CSV", "JSON"], horizontal=True)

    selected_labels = [l for l in report_dict.keys() if st.session_state.get(f"cb_{l}")]

    if not selected_labels:
        st.error("Selecione pelo menos uma categoria.")
        return

    # As linhas nascem do conjunto auditado inteiro — já deduplicado e enriquecido
    # com o PyPI — e a seleção apenas filtra. Assim uma dependência que cai em duas
    # categorias (ex.: Zumbi e Desatualizada) continua exportando uma única linha.
    export_rows = build_export_rows(
        report_dict[ALL_LABEL],
        zombies=report_dict[CATEGORY_NAMES["zombies"]],
        ghosts=report_dict[CATEGORY_NAMES["ghosts"]],
        project_name=st.session_state.get("project_name", "N/A"),
        analysis_date=st.session_state.get("analysis_date", "N/A"),
    )

    if st.session_state.get(f"cb_{ALL_LABEL}"):
        final_list = export_rows
    else:
        selected_categories = {
            EXPORT_CATEGORIES[label]
            for label in selected_labels
            if label in EXPORT_CATEGORIES
        }
        include_outdated = CATEGORY_NAMES["outdated"] in selected_labels
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
        label=f"Baixar Relatório ({len(final_list)} itens) .{file_ext} 📥",
        data=exported_data,
        file_name=f"report_dp_auditor.{file_ext}",
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
