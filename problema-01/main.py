"""
This is the main entry point for the application.
"""

import streamlit as st

# 1. Configurações iniciais da página (opcional, mas recomendado)
st.set_page_config(page_title="DP-Auditor", page_icon="🔍", layout="wide")


pg = st.navigation(
    [
        st.Page("pages/home.py", title="Página Inicial", default=True),
        st.Page("pages/report.py", title="Relatório da Análise"),
        st.Page("pages/loading.py", title="Carregamento", visibility="hidden"),
    ]
)

pg.run()
