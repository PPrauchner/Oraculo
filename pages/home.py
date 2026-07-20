"""
Módulo responsável pela página inicial da aplicação.


Permite ao usuário:
- Informar o Projeto-Alvo por upload de archive ou por diretório local (ADR-0001)
- Configurar opções de análise (Exclusões, etc.)


Entrada:
- Interação do usuário


Saída:
- Dados iniciais para execução da análise
"""

from pathlib import Path

import streamlit as st
from utils.sidebar import sidebar
from utils.functions import EXTRATORES
from utils.messages import format_error
from utils.i18n import t
from core.ingestion.decompressor import process_uploaded_file
from core.ingestion.filter import get_unique_folders, validate_project_structure
from core.ingestion.source import ProjectSource, open_directory

sidebar()

# Valor estável do modo de ingestão, não rótulo. Ele é comparado por igualdade logo
# abaixo e vai parar em `st.session_state["ingestion_mode"]`: se fosse o texto da
# tela, trocar de língua quebraria a comparação e guardaria rótulo traduzido no
# estado, que é justamente o que ADR-0009 proíbe. O rótulo nasce no `format_func`.
UPLOAD_MODE = "upload"
DIRECTORY_MODE = "directory"


def _mode_label(mode: str) -> str:
    """Rótulo de um modo de ingestão na língua da tela."""
    return t(f"home.mode.{mode}")


def principal_interface():
    st.title(t("home.title"))
    st.write(t("home.intro"))


def _clear_source():
    """Esquece o Projeto-Alvo: nada a auditar até que uma fonte válida entre."""
    st.session_state["archive"] = None
    st.session_state["folder_list"] = []
    st.session_state["archive_is_valid"] = False


def _load_source(source: ProjectSource, project_name: str) -> None:
    """Registra a fonte do Projeto-Alvo e confere os requisitos mínimos.

    Args:
        source: Fonte do Projeto-Alvo (archive aberto ou Path de diretório).
        project_name: Identidade do Projeto-Alvo na exportação.
    """
    st.session_state["archive"] = source
    st.session_state["folder_list"] = get_unique_folders(source)
    st.session_state["project_name"] = project_name

    ignore_folders = st.session_state.get("ignore_folders", [])
    is_valid, error = validate_project_structure(source, ignore_folders)
    st.session_state["archive_is_valid"] = is_valid

    if error is not None:
        st.error(format_error(error))


def _entering_by_upload():
    """Recebe o Projeto-Alvo compactado."""
    file = st.file_uploader(
        t("home.upload.label"),
        type=[key for key in EXTRATORES.keys()],
        key="file_uploaded",
    )

    if not file:
        _clear_source()
        return

    archive = process_uploaded_file(file)
    if not archive:
        st.error(t("home.upload.failed"))
        _clear_source()
        return

    # Identidade do Projeto-Alvo na exportação: o nome do arquivo sem a
    # extensão (".tar.gz" deixa um ".tar" residual no stem).
    _load_source(archive, Path(file.name).stem.removesuffix(".tar"))


def _entering_by_directory():
    """Recebe o Projeto-Alvo apontando para o diretório do código (US-01)."""
    typed_path = st.text_input(
        t("home.directory.label"),
        key="project_directory",
        placeholder=t("home.directory.placeholder"),
        help=t("home.directory.help"),
    )

    if not typed_path.strip():
        _clear_source()
        return

    directory, error = open_directory(typed_path)
    if error is not None:
        st.error(format_error(error))
        _clear_source()
        return

    _load_source(directory, directory.resolve().name)


def entering_data():
    # A coluna da fonte carrega o campo de caminho e a dropzone, que precisam de
    # largura; a das Configurações carrega uma linha — ou o multiselect, ou a frase
    # que explica por que ele ainda não está lá.
    col1, col2 = st.columns([2, 1])

    # `border=True` é a moldura da API: a cor sai do `borderColor` do tema e segue os
    # modos claro e escuro sozinha, sem folha de estilo própria (issue #39).
    with col1.container(border=True):
        st.subheader(t("home.source.header"))
        # Uma fonte por vez: com os dois campos visíveis, "qual vale quando os
        # dois estão preenchidos" vira uma pergunta sem resposta óbvia.
        mode = st.radio(
            t("home.mode.label"),
            [UPLOAD_MODE, DIRECTORY_MODE],
            horizontal=True,
            key="ingestion_mode",
            format_func=_mode_label,
        )

        if mode == UPLOAD_MODE:
            _entering_by_upload()
        else:
            _entering_by_directory()

    with col2.container(border=True):
        st.subheader(t("home.settings.header"))
        opcoes = st.session_state.get("folder_list", [])

        # Trocar de Projeto-Alvo troca as pastas oferecidas; uma Exclusão marcada
        # que não existe mais na nova fonte quebraria o multiselect.
        selecionadas = st.session_state.get("ignore_folders", [])
        if any(folder not in opcoes for folder in selecionadas):
            st.session_state["ignore_folders"] = [
                folder for folder in selecionadas if folder in opcoes
            ]

        # A Exclusão não tem o que oferecer antes de existir uma fonte: um multiselect
        # sem opção lê-se como controle quebrado, e não como etapa ainda não cumprida.
        if opcoes:
            st.multiselect(
                t("home.settings.ignore_folders"),
                options=opcoes,
                key="ignore_folders",
            )
        else:
            st.caption(t("home.settings.no_source"))


def principal_action():
    # Destaque e largura saem do próprio Streamlit: `type="primary"` pinta o botão
    # com a cor primária da paleta, que o tema já adapta aos dois modos. Era isto
    # que o CSS injetado fazia à mão, com um azul só dele.
    if st.button(t("home.run"), type="primary", width="stretch"):
        if st.session_state.get("archive") is None:
            st.error(t("home.run.no_source"))
        elif not st.session_state.get("archive_is_valid", False):
            st.error(t("home.run.invalid_source"))
        else:
            st.switch_page("pages/loading.py")


principal_interface()
st.divider()
entering_data()
principal_action()
