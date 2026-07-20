"""
This is the main entry point for the application.
"""

import streamlit as st

from utils.i18n import t

# 1. Configurações iniciais da página (opcional, mas recomendado)
st.set_page_config(page_title="ORÁCULO", page_icon="🔍", layout="wide")


# `st.navigation` roda antes de qualquer página, então a língua precisa resolver
# aqui — e resolve: `t()` lê de `st.query_params`, que já está disponível neste
# ponto. É o que faz o menu lateral acompanhar `?lang=` junto com o resto da tela.
pg = st.navigation(
    [
        st.Page("pages/home.py", title=t("nav.home"), default=True),
        st.Page("pages/report.py", title=t("nav.report")),
        st.Page("pages/loading.py", title=t("nav.loading"), visibility="hidden"),
    ]
)

pg.run()
