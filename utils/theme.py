"""
Leitura da paleta única do tema.

A paleta é declarada em `.streamlit/config.toml` e o Streamlit já a aplica sozinho
aos componentes nativos. Este módulo existe para os poucos lugares que precisam da
cor como valor — o donut do Plotly, que recebe um mapa de cores explícito, e o
HTML do carregamento.

Responsabilidades:
- Resolver um token semântico do tema (`blueColor`, `violetColor`, …) na cor da paleta.
- Traduzir as Categorias do relatório em cores prontas para o gráfico.
"""

import streamlit as st

from utils.constants import STATUS_COLOR_TOKENS


def theme_color(token: str) -> str:
    """Resolve um token semântico do tema na cor declarada na paleta.

    Args:
        token: Nome do token do Streamlit, sem o prefixo `theme.` (ex.: "blueColor").

    Returns:
        A cor do token, como declarada em `.streamlit/config.toml`.

    Raises:
        KeyError: Se o token não estiver na paleta. Falhar aqui é proposital: uma
            cor ausente viraria `None`, o Plotly cairia no default dele e a
            divergência de paleta voltaria sem ninguém perceber.
    """
    color = st.get_option(f"theme.{token}")

    if color is None:
        raise KeyError(f"token '{token}' não está na paleta de .streamlit/config.toml")

    return color


def status_colors() -> dict[str, str]:
    """Mapeia cada Categoria do relatório na cor da paleta.

    Returns:
        Rótulo da Categoria (como o donut o exibe) -> cor.
    """
    return {label: theme_color(token) for label, token in STATUS_COLOR_TOKENS.items()}
