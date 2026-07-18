"""
Módulo de interface de carregamento e orquestração de análise.

Gerencia a execução do pipeline completo de análise de dependências,
incluindo feedback visual ao usuário durante o processamento.
"""

import time
from datetime import datetime
import streamlit as st
from utils.sidebar import sidebar
from core.parsin.declaration_collector import collect_declarations
from core.parsin.lock_resolver import build_lock_version_map, resolve_used_versions
from core.parsin.import_parser import parse_imports_with_filter
from core.analysis.zombie_analizer import analyze_zombie_dependencies
from core.analysis.ghost_analizer import analyze_ghost_dependencies
from core.analysis.outdated_analizer import analyze_dependency_status
from core.ingestion.filter import validate_archive_structure

sidebar()


def _validate_archive_requirements(archive) -> bool:
    """
    Valida se o arquivo contém os requisitos mínimos para análise.

    Função de segurança adicional que verifica:
    1. Arquivo não é None
    2. Arquivo contém pelo menos um .py
    3. Arquivo contém arquivo de dependências

    Args:
        archive: Objeto ZipFile ou TarFile

    Returns:
        True se válido, False caso contrário
        (Exibe mensagem de erro antes de retornar False)
    """
    ignore_folders = st.session_state.get("ignore_folders", [])
    is_valid, error_msg = validate_archive_structure(archive, ignore_folders)

    if not is_valid:
        st.error(error_msg)
        return False

    return True


def _render_progress_steps(step_labels: list[str], current_step: int) -> str:
    """
    Gera HTML para renderizar o progresso visual das etapas de análise.

    Args:
        step_labels: Lista de descrições das etapas (ex: ["1. Parsing...", "2. Scanning..."]).
        current_step: Índice (0-based) da etapa atual em processamento.

    Returns:
        String contendo HTML com styling inline para exibição no Streamlit.
    """
    html = '<div class="main-loader"><div class="loader-ring"></div><div style="font-size:2.0rem; font-weight:bold; margin-bottom:15px;">Analysis in Progress...</div><div class="step-list">'
    for j, label in enumerate(step_labels):
        if j < current_step:
            color, opacity, cursor = "#4CAF50", "1", " ✅"
        elif j == current_step:
            color, opacity, cursor = "#5dade2", "1", " ▌"
        else:
            color, opacity, cursor = "#ffffff", "0.3", ""

        weight = "bold" if j == current_step else "normal"
        html += f'<div style="color:{color}; opacity:{opacity}; font-weight:{weight}">{label}{cursor}</div>'

    html += "</div></div></div>"
    return html


def _execute_analysis_pipeline() -> None:
    """
    Executa o pipeline completo de análise de dependências.

    Orquestração sequencial de etapas:
    1. Localizar arquivo de dependências
    2. Extrair imports do código-fonte
    3. Identificar dependências zumbis
    4. Identificar dependências fantasmas
    5. Consultar PyPI para versões atualizadas

    Popula st.session_state com chaves:
    - declared_dependencies: Dependências normalizadas do arquivo
    - imports: Imports encontrados no código
    - zombies: Dependências declaradas mas não usadas
    - ghosts: Imports sem declaração correspondente
    - all_dependencies: Todas with status e versões PyPI
    - analysis_complete: Flag indicando sucesso

    Raises:
        Nenhuma exceção é lançada (para Streamlit); mensagens de erro
        são exibidas via st.error().
    """
    step_labels = [
        "1. Localizando arquivo de dependências...",
        "2. Extraindo imports do código-fonte...",
        "3. Analisando dependências zumbis...",
        "4. Identificando dependências fantasmas...",
        "5. Consultando PyPI para versões...",
    ]

    placeholder = st.empty()
    archive = st.session_state.get("archive")

    if archive is None:
        st.error(
            "❌ Nenhum arquivo foi processado. Volte para Home e faça upload de um arquivo compactado válido."
        )
        st.stop()

    # Validação de segurança: verificar requisitos mínimos
    if not _validate_archive_requirements(archive):
        st.stop()

    ignore_folders = st.session_state.get("ignore_folders", [])

    try:
        placeholder.markdown(
            _render_progress_steps(step_labels, 0), unsafe_allow_html=True
        )
        time.sleep(1.0)

        declared_dependencies = collect_declarations(archive, ignore_folders)
        if not declared_dependencies:
            st.error(
                "❌ Nenhuma Declaração encontrada (requirements.txt, pyproject.toml ou "
                "environment.yml). O Lock sozinho não define o conjunto auditado."
            )
            st.stop()

        # O Lock resolve a Versão Usada de cada pacote do conjunto (ADR-0002); sem
        # ele, só um pin define a versão e o resto fica N/D.
        lock_versions = build_lock_version_map(archive, ignore_folders)
        declared_dependencies = resolve_used_versions(
            declared_dependencies, lock_versions
        )

        st.session_state["declared_dependencies"] = declared_dependencies

        placeholder.markdown(
            _render_progress_steps(step_labels, 1), unsafe_allow_html=True
        )
        time.sleep(1.0)

        imports = parse_imports_with_filter(archive, ignore_folders)
        st.session_state["imports"] = imports

        placeholder.markdown(
            _render_progress_steps(step_labels, 2), unsafe_allow_html=True
        )
        time.sleep(1.0)

        zombies = analyze_zombie_dependencies(declared_dependencies, imports)
        st.session_state["zombies"] = zombies

        placeholder.markdown(
            _render_progress_steps(step_labels, 3), unsafe_allow_html=True
        )
        time.sleep(1.0)

        ghosts = analyze_ghost_dependencies(declared_dependencies, imports)
        st.session_state["ghosts"] = ghosts

        placeholder.markdown(
            _render_progress_steps(step_labels, 4), unsafe_allow_html=True
        )
        time.sleep(1.0)

        all_deps = declared_dependencies + ghosts
        seen = set()
        unique_deps = []
        for dep in all_deps:
            pkg_name = dep["Pacote"].lower()
            if pkg_name not in seen:
                seen.add(pkg_name)
                unique_deps.append(dep)

        all_dependencies_with_status = analyze_dependency_status(unique_deps)
        st.session_state["all_dependencies"] = all_dependencies_with_status

        # Eixo temporal da US-07: a exportação carimba quando a análise rodou, não
        # quando o arquivo foi baixado. Precisão de segundos separa duas execuções
        # do mesmo Projeto-Alvo no mesmo dia.
        st.session_state["analysis_date"] = datetime.now().isoformat(timespec="seconds")
        st.session_state["analysis_complete"] = True

        placeholder.markdown(
            _render_progress_steps(step_labels, 5), unsafe_allow_html=True
        )
        time.sleep(0.5)

    except Exception as e:
        st.error(f"❌ Erro durante a análise: {str(e)}")
        st.session_state["analysis_complete"] = False
        st.stop()


def _render_loading_ui() -> None:
    """
    Renderiza a interface visual de carregamento e inicia a análise.

    Exibe spinner, título e progresso das etapas. Após conclusão,
    redireciona para a página de relatório.
    """

    st.markdown(
        """<style>
    /* Centraliza sem quebrar sidebar */
    [data-testid="stMain"] {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
    }

    /* Loader */
    .main-loader {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at center, #1a3a3a 0%, #0e1117 50%);
        color: white;
        font-family: 'Inter', sans-serif;
        padding: 80px;
        border-radius: 10px;
        min-height: 150vh;
    }

    .loader-ring {
        width: 250px;
        height: 250px;
        border: 5px solid rgba(255,255,255,0.1);
        border-top: 5px solid #3498db;
        border-right: 5px solid #2ecc71;
        border-radius: 70%;
        animation: spin 1.5s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .step-list {
     font-family: 'Roboto', sans-serif;
        line-height: 1.6;
        text-align: left;
        width: 450px;
        margin-top: 10px;
        font-size: 1.0rem;
    }

    </style>
    """,
        unsafe_allow_html=True,
    )

    _execute_analysis_pipeline()

    st.markdown("</div>", unsafe_allow_html=True)
    time.sleep(0.5)
    st.switch_page("pages/report.py")


if not st.session_state.get("archive"):
    st.error("❌ Arquivo não encontrado!")
    st.stop()

_render_loading_ui()
