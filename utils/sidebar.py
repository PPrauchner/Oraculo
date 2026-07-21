"""
Application sidebar.

Defines and renders the sidebar used on all pages,
including navigation and configuration options.

Input:
- Application state

Output:
- Reusable visual component
"""

from utils.icons import SVG_LUPA
from utils.i18n import LANGUAGE_PARAM, available_languages, current_language, t, translate
from utils.theme import theme_color
import streamlit as st


def language_selector() -> None:
    """Offers the available languages and stores the choice in the URL.

    Each option appears in its own language (`language.name`), so adding a
    file in `locales/` is enough for the language to appear here — with no new `if` (ADR-0009).
    The widget does not use `key`: the language lives in `?lang=`, and having both storing the
    same thing would create two sources of truth that disagree on refresh.
    """
    languages = available_languages()
    current = current_language()

    chosen = st.selectbox(
        t("sidebar.language"),
        options=languages,
        index=languages.index(current),
        format_func=lambda language: translate("language.name", language),
    )

    if chosen != current:
        st.query_params[LANGUAGE_PARAM] = chosen

        # The sidebar runs before the page body, so the `st.rerun()` below
        # aborts the script before the page registers its widgets — and Streamlit
        # discards the state of every widget that was not registered in the run. Without
        # reasserting the keys, changing the language would erase the loaded Target Project and
        # the marked Exclusions: an appearance selector cannot cost the work
        # already done. Reassigning marks the key as set by the user, which is what
        # makes it survive.
        for key in list(st.session_state.keys()):
            st.session_state[key] = st.session_state[key]

        # Without the rerun the screen comes out half in each language: what was already rendered
        # above read the old parameter. There is no loop — after the rerun the choice and the
        # URL agree, and the condition becomes false.
        st.rerun()


def sidebar() -> None:
    """
    Renders the application sidebar.
    It displays the title, a description and a settings section where the user can select folders to be ignored during the dependency analysis.
    The function also disables folder selection when the user is outside the home page.

    Args:
        pagina_atual (str, optional): Identifier of the current page for state control. Defaults to "home".

    Returns:
        None

    """
    with st.sidebar:

        # The magnifying glass inherits this color via `currentColor`, so title and icon come from the
        # same source — the palette's primary color.
        st.markdown(
            f'<h1 style="display: flex; align-items: center; color: {theme_color("primaryColor")}">{SVG_LUPA} ORÁCULO</h1>',
            unsafe_allow_html=True,
        )

        st.markdown(t("sidebar.subtitle"))

        language_selector()

        # Caption, not control: the theme belongs to Streamlit's native mechanism, which already
        # stores the choice per session in the visitor's browser. `theme.base` is
        # `scriptable = False`, so there is no toggle of our own to offer here — what
        # is missing is saying where what already exists lives. The menu path (`Settings →
        # Theme`) stays in English in both locales on purpose: it is the literal label that
        # Streamlit draws on the screen, and translating it would point to something nonexistent.
        st.caption(t("sidebar.theme_hint"))

        st.divider()
