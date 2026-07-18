"""
Módulo responsável pela página inicial da aplicação.


Permite ao usuário:
- Fazer upload do arquivo ZIP
- Configurar opções de análise (exclusões, etc.)


Entrada:
- Interação do usuário


Saída:
- Dados iniciais para execução da análise
"""

from pathlib import Path

import streamlit as st
from utils.sidebar import sidebar
from utils.functions import EXTRATORES
from core.ingestion.decompressor import process_uploaded_file, get_archive_files
from core.ingestion.filter import get_unique_folders, validate_archive_structure

sidebar()


def visual_css():
    st.markdown(
        """
        <style>
        .stDropzone, .stTextInput>div { border-radius: 10px !important; background: #1e1e1e !important; }
        .stButton>button { width: 100%; background: #1a73e8 !important; color: white !important; font-weight: bold; height: 3em; }
        </style>
    """,
        unsafe_allow_html=True,
    )


def principal_interface():
    st.title("🚀 Iniciar Auditoria")
    st.write("Suba o arquivo do seu projeto para uma análise")


def entering_data():
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.subheader("Realize o Upload do Projeto")
        file = st.file_uploader(
            "Zip, tar.gz ou tar",
            type=[key for key in EXTRATORES.keys()],
            key="file_uploaded",
        )

    if file:
        archive = process_uploaded_file(file)

        if archive:
            file_list = get_archive_files(archive)
            folders = get_unique_folders(file_list)

            st.session_state["archive"] = archive
            st.session_state["file_list"] = file_list
            st.session_state["folder_list"] = folders
            # Identidade do Projeto-Alvo na exportação: o nome do arquivo sem a
            # extensão (".tar.gz" deixa um ".tar" residual no stem).
            st.session_state["project_name"] = Path(file.name).stem.removesuffix(".tar")

            # Validar requisitos mínimos
            ignore_folders = st.session_state.get("ignore_folders", [])
            is_valid, error_msg = validate_archive_structure(archive, ignore_folders)

            st.session_state["archive_is_valid"] = is_valid

            if not is_valid:
                st.error(error_msg)
        else:
            st.error("Erro ao processar arquivo")
            st.session_state["archive_is_valid"] = False
    else:
        st.session_state["archive"] = None
        st.session_state["file_list"] = []
        st.session_state["folder_list"] = []
        st.session_state["archive_is_valid"] = False

    with col2:
        st.subheader("Configurações")
        opcoes = st.session_state.get("folder_list", [])
        st.multiselect(
            "Pastas a ignorar:",
            options=opcoes,
            key="ignore_folders",
        )


def principal_action():
    if st.button("Executar Análise Completa"):
        if st.session_state.get("file_uploaded") is None:
            st.error("Por favor, suba um arquivo para análise.")
        elif not st.session_state.get("archive_is_valid", False):
            st.error(
                "❌ Não é possível executar a análise. Certifique-se de que o arquivo atende aos requisitos mínimos."
            )
        else:
            st.switch_page("pages/loading.py")


visual_css()
principal_interface()
st.divider()
entering_data()
principal_action()
