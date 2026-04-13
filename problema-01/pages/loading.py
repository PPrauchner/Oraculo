"""
Módulo de interface de carregamento e orquestração de análise.

Gerencia a execução do pipeline completo de análise de dependências,
incluindo feedback visual ao usuário durante o processamento.
"""

import time
import streamlit as st
from utils.sidebar import sidebar
from utils.functions import READERS
import core.parsin.readers
from core.parsin.dependency_parser import parse_dependencies
from core.parsin.import_parser import parse_imports_with_filter
from core.analysis.zombie_analizer import analyze_zombie_dependencies
from core.analysis.ghost_analizer import analyze_ghost_dependencies
from core.analysis.outdated_analizer import analyze_dependency_status
from core.ingestion.decompressor import get_archive_files
from core.ingestion.filter import is_path_in_ignored_folders

sidebar()


def _find_dependency_file(archive) -> tuple[str | None, list]:
    """
    Localiza e extrai dependências declaradas do arquivo principal de configuração.

    Busca por requirements.txt ou arquivos .lock respeitando
    pastas ignoradas configuradas pelo usuário.

    Args:
        archive: Objeto zipfile.ZipFile ou tarfile.TarFile do projeto compactado.

    Returns:
        Tupla (caminho_do_arquivo, lista_dependências). Se não encontrado,
        retorna (None, []).

    Raises:
        Nenhuma exceção é lançada; erros são silenciosamente ignorados.
    """

    if archive is None:
        st.error(
            "❌ Erro: O arquivo não foi processado corretamente. Certifique-se de enviar um ZIP, TAR ou TAR.GZ válido."
        )
        st.stop()

    ignore_folders = st.session_state.get("ignore_folders", [])

    try:
        file_list = get_archive_files(archive)
        if not file_list:
            st.error("❌ O arquivo compactado está vazio.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Erro ao ler arquivos: {str(e)}")
        st.stop()

    for member in file_list:
        file_path = getattr(member, "filename", None) or getattr(member, "name", None)
        if not file_path:
            continue

        if is_path_in_ignored_folders(file_path, ignore_folders):
            continue

        file_name = file_path.lower()

        for extension, reader_func in READERS.items():
            if file_name.endswith(extension):
                try:
                    if hasattr(member, "filename"):
                        content = archive.read(member.filename).decode(
                            "utf-8", errors="ignore"
                        )
                    else:
                        f = archive.extractfile(member)
                        if f is None:
                            continue
                        content = f.read().decode("utf-8", errors="ignore")

                    dependencies = reader_func(content)
                    if dependencies:
                        return file_path, dependencies
                except Exception:
                    continue

    return None, []


def _render_progress_steps(step_labels: list[str], current_step: int) -> str:
    """
    Gera HTML para renderizar o progresso visual das etapas de análise.

    Args:
        step_labels: Lista de descrições das etapas (ex: ["1. Parsing...", "2. Scanning..."]).
        current_step: Índice (0-based) da etapa atual em processamento.

    Returns:
        String contendo HTML com styling inline para exibição no Streamlit.
    """
    html = '<div class="main-loader"><div class="loader-ring"></div><div style="font-size:1.5rem; font-weight:bold; margin-bottom:15px;">Analysis in Progress...</div><div class="step-list">'
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

    ignore_folders = st.session_state.get("ignore_folders", [])

    try:
        placeholder.markdown(
            _render_progress_steps(step_labels, 0), unsafe_allow_html=True
        )
        time.sleep(1.0)

        dep_file_path, raw_dependencies = _find_dependency_file(archive)
        if not raw_dependencies:
            st.error(
                "❌ Nenhum arquivo de dependências encontrado (requirements.txt ou .lock)"
            )
            st.stop()

        declared_dependencies = parse_dependencies(raw_dependencies)
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
        """
        <style>
        * { margin: 0 !important; padding: 0 !important; }
        html, body { overflow: hidden !important; height: 100vh !important; width: 100vw !important; }
        [data-testid="stAppViewContainer"] { overflow: hidden !important; height: 100vh !important; }
        [data-testid="stMain"] { overflow: hidden !important; height: 100vh !important; padding: 0 !important; }
        .main-loader { position: fixed !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; background: radial-gradient(circle at center, #1a3a3a 0%, #0e1117 70%) !important; color: white !important; font-family: 'Inter', sans-serif !important; z-index: 9999 !important; padding: 40px !important; border-radius: 10px !important; }
        .loader-ring { width: 70px !important; height: 70px !important; border: 5px solid rgba(255,255,255,0.1) !important; border-top: 5px solid #3498db !important; border-right: 5px solid #2ecc71 !important; border-radius: 50% !important; animation: spin 1.5s linear infinite !important; margin-bottom: 5px !important; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .step-list { font-family: 'Courier New', monospace !important; line-height: 1.6 !important; text-align: left !important; width: 450px !important; margin-top: 5px !important; font-size: 0.9rem !important; }
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
