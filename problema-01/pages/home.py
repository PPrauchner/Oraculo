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

import streamlit as st
from utils_gui.sidebar import sidebar
from utils_gui.constants import ARQUIVOS

st.set_page_config(page_title="Baita Auditor", layout="wide")
sidebar()


def visual_css():
    st.markdown(
        """
    <style>
    .stDropzone, .stTextInput>div { border-radius: 10px !important; background: #1e1e1e !important; }
    .stButton>button { width: 100%; background: #1a73e8 !important; color: white !important; font-weight: bold; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def principal_interface():
    st.title("Iniciar Auditoria do Projeto")
    st.write(
        "Suba seu arquivo de configuração e indique o caminho do código para analisar as dependências."
    )


def entering_data():
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.file_uploader(
            "Arraste ou clique para subir pyproject.toml / requirements.txt",
            type=["zip", "tar", "tar.gz"],
            key="file_upload",
        )
    with col2:
        st.subheader("Configurações")
        st.multiselect(
            "Pastas a ignorar:", ARQUIVOS if ARQUIVOS else [], key="ignore_folders"
        )


def principal_action():
    if st.button("Iniciar Auditoria 🚀"):
        if not st.session_state.get("file_upload"):
            st.error("Por favor, suba um arquivo para análise.")
            return
        st.session_state["file_uploaded"] = True
        st.switch_page("pages/loading.py")
        


visual_css()
principal_interface()
entering_data()
principal_action()
