"""
Módulo responsável pela sidebar da aplicação.

Define e renderiza a barra lateral utilizada em todas as páginas,
incluindo navegação e opções de configuração.


"""

from utils.constants import BLUE
from utils.constants import SVG_LUPA
import streamlit as st


def sidebar() -> None:
    """
    Função responsável por renderizar a barra lateral da aplicação.
    Ela exibe o título, uma descrição e uma seção de configurações onde o usuário pode selecionar pastas a serem ignoradas durante a análise de dependências.
    A função também desabilita a seleção de pastas quando o usuário está fora da página inicial.

    Args:
        pagina_atual (str, optional): Identificador da página atual para controle de estado. Defaults to "home".

    Returns:
        None

    """
    with st.sidebar:

        st.markdown(
            f'<h1 style="display: flex; align-items: center; color: {BLUE}">{SVG_LUPA} DP-Auditor</h1>',
            unsafe_allow_html=True,
        )

        st.markdown("Auditoria de Dependências Python")

        st.divider()

    st.sidebar.info("Dica: Ignore pastas de ambiente virtual para acelerar a análise.")
