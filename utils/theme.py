"""
Reading of the theme's single palette.

The palette is declared in `.streamlit/config.toml` and Streamlit already applies it on its own
to the native components. This module exists for the few places that need the
color as a value — the Plotly donut, which receives an explicit color map, and the
loading HTML.

Responsibilities:
- Resolve a semantic theme token (`blueColor`, `violetColor`, …) into the palette color.
- Translate the report Categories into colors ready for the chart.
"""

import streamlit as st

from utils.constants import STATUS_COLOR_TOKENS


def theme_color(token: str) -> str:
    """Resolves a semantic theme token into the color declared in the palette.

    Args:
        token: Name of the Streamlit token, without the `theme.` prefix (e.g.: "blueColor").

    Returns:
        The token's color, as declared in `.streamlit/config.toml`.

    Raises:
        KeyError: If the token is not in the palette. Failing here is intentional: a
            missing color would become `None`, Plotly would fall back to its default and the
            palette divergence would return without anyone noticing.
    """
    color = st.get_option(f"theme.{token}")

    if color is None:
        raise KeyError(f"token '{token}' não está na paleta de .streamlit/config.toml")

    return color


def status_colors() -> dict[str, str]:
    """Maps each report Category to the palette color.

    Returns:
        Category label (as the donut displays it) -> color.
    """
    return {label: theme_color(token) for label, token in STATUS_COLOR_TOKENS.items()}
