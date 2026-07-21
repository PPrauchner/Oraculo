"""
This is the main entry point for the application.
"""

import streamlit as st

from utils.i18n import t
from utils.icons import SVG_LUPA
from utils.layout import apply_layout

# 1. Configurações iniciais da página (opcional, mas recomendado)
# O ícone da aba é a mesma lupa SVG do título da sidebar (issue #45): um só desenho, sem
# emoji. `set_page_config` aceita string SVG e a rasteriza como favicon.
st.set_page_config(page_title="ORÁCULO", page_icon=SVG_LUPA, layout="wide")

# Ponto único do CSS de layout: daqui a folha vale para todas as páginas, então
# nenhuma delas precisa (nem pode) declarar a sua. Depois do `set_page_config`, que
# tem de vir primeiro, e antes do `pg.run()`, para valer já na primeira pintura.
apply_layout()


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
