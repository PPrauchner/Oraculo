"""
Módulo de interface de carregamento e orquestração de análise.

Gerencia a execução do pipeline completo de análise de dependências,
incluindo feedback visual ao usuário durante o processamento.
"""

from datetime import datetime
import streamlit as st
from utils.sidebar import sidebar
from utils.i18n import t
from utils.messages import format_error
from utils.theme import theme_color
from core.parsin.declaration_collector import collect_declarations
from core.parsin.lock_resolver import build_lock_version_map, resolve_used_versions
from core.parsin.import_parser import parse_imports_with_filter
from core.analysis.zombie_analizer import analyze_zombie_dependencies
from core.analysis.ghost_analizer import analyze_ghost_dependencies
from core.analysis.outdated_analizer import analyze_dependency_status
from core.ingestion.filter import validate_project_structure

sidebar()

# Nome estável de cada etapa do pipeline, na ordem em que ela roda. O texto que o
# usuário lê sai do locale na hora de desenhar; aqui fica só a identidade da etapa.
STEP_KEYS = ("declarations", "imports", "zombies", "ghosts", "pypi")


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
    is_valid, error = validate_project_structure(archive, ignore_folders)

    if error is not None:
        st.error(format_error(error))
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
    done_color = theme_color("greenColor")
    current_color = theme_color("blueColor")

    html = f'<div class="main-loader"><div class="loader-ring"></div><div style="font-size:2.0rem; font-weight:bold; margin-bottom:15px;">{t("loading.in_progress")}</div><div class="step-list">'
    for j, label in enumerate(step_labels):
        if j < current_step:
            color, opacity, cursor = done_color, "1", " ✅"
        elif j == current_step:
            color, opacity, cursor = current_color, "1", " ▌"
        else:
            # A etapa pendente herda a cor de texto do tema — fixar branco a
            # apagava no modo claro.
            color, opacity, cursor = "inherit", "0.45", ""

        weight = "bold" if j == current_step else "normal"
        html += f'<div style="color:{color}; opacity:{opacity}; font-weight:{weight}">{label}{cursor}</div>'

    html += "</div></div>"
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
    step_labels = [t(f"loading.step.{step}") for step in STEP_KEYS]

    placeholder = st.empty()
    archive = st.session_state.get("archive")

    if archive is None:
        st.error(t("loading.error.not_processed"))
        st.stop()

    # Validação de segurança: verificar requisitos mínimos
    if not _validate_archive_requirements(archive):
        st.stop()

    ignore_folders = st.session_state.get("ignore_folders", [])

    try:
        # Cada etapa é anunciada antes do próprio trabalho e cede a vez à seguinte
        # quando ele termina de fato — sem tempo mínimo de exibição. Projeto pequeno
        # pisca porque a auditoria é rápida mesmo; esconder isso seria mentir. Não
        # reintroduzir atraso para "consertar o flicker" (issue #34).
        placeholder.markdown(
            _render_progress_steps(step_labels, 0), unsafe_allow_html=True
        )

        declared_dependencies = collect_declarations(archive, ignore_folders)
        if not declared_dependencies:
            st.error(t("loading.error.no_declaration"))
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

        imports = parse_imports_with_filter(archive, ignore_folders)
        st.session_state["imports"] = imports

        placeholder.markdown(
            _render_progress_steps(step_labels, 2), unsafe_allow_html=True
        )

        zombies = analyze_zombie_dependencies(declared_dependencies, imports)
        st.session_state["zombies"] = zombies

        placeholder.markdown(
            _render_progress_steps(step_labels, 3), unsafe_allow_html=True
        )

        ghosts = analyze_ghost_dependencies(declared_dependencies, imports)
        st.session_state["ghosts"] = ghosts

        placeholder.markdown(
            _render_progress_steps(step_labels, 4), unsafe_allow_html=True
        )

        all_deps = declared_dependencies + ghosts
        seen = set()
        unique_deps = []
        for dep in all_deps:
            pkg_name = dep["package"].lower()
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

    except Exception as e:
        st.error(t("loading.error.failed").format(reason=e))
        st.session_state["analysis_complete"] = False
        st.stop()


def _render_loading_ui() -> None:
    """
    Renderiza a interface visual de carregamento e inicia a análise.

    Exibe spinner, título e progresso das etapas. Após conclusão,
    redireciona para a página de relatório.
    """

    # Só o que o tema não consegue declarar: o layout do bloco e a animação do anel.
    # Nada de cor de fundo, cor de texto ou fonte — isso o tema já resolve, e era
    # justamente o que fazia a tela nascer escura no modo claro (issue #39). As
    # cores do anel saem da paleta única.
    st.markdown(
        f"""<style>
    .main-loader {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 32px 16px;
    }}

    .loader-ring {{
        width: 120px;
        height: 120px;
        border: 5px solid {theme_color("grayColor")};
        border-top: 5px solid {theme_color("blueColor")};
        border-right: 5px solid {theme_color("greenColor")};
        border-radius: 50%;
        animation: spin 1.5s linear infinite;
        margin-bottom: 24px;
    }}

    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}

    .step-list {{
        line-height: 1.6;
        text-align: left;
        max-width: 450px;
        margin-top: 10px;
    }}

    </style>
    """,
        unsafe_allow_html=True,
    )

    _execute_analysis_pipeline()

    st.switch_page("pages/report.py")


if st.session_state.get("archive") is None:
    st.error(t("loading.error.source_missing"))
    st.stop()

_render_loading_ui()
