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


def _apply_language() -> None:
    """Copies the picked language into `?lang=`, the single source the screen reads.

    Runs in the selectbox `on_change`, which Streamlit fires before the rerun that follows a
    real interaction. Writing the param before the body re-runs is what makes the next run
    read the new language from top to bottom — the screen comes out whole in the new language,
    not half in each (issue #53).
    """
    st.query_params[LANGUAGE_PARAM] = st.session_state["language_choice"]


def language_selector() -> None:
    """Offers the available languages and stores the choice in the URL.

    Each option appears in its own language (`language.name`), so adding a
    file in `locales/` is enough for the language to appear here — with no new `if` (ADR-0009).

    `?lang=` stays the single source of truth for the rendered language: `current_language()`
    reads it and every label resolves from it at render time. The selectbox carries a `key`
    only so its `on_change` can copy the pick into the URL, and `index` seeds it from `?lang=`
    on a fresh session, so a shared link opens with the selector already on its language. The
    rerun Streamlit fires for a real interaction carries the widget states, so the loaded Target
    Project and the marked Exclusions survive by the normal compaction — no manual `st.rerun()`
    and no reasserting the whole state, which is what used to crash the `file_uploader` (issue #53).
    """
    languages = available_languages()
    current = current_language()

    st.selectbox(
        t("sidebar.language"),
        options=languages,
        index=languages.index(current),
        format_func=lambda language: translate("language.name", language),
        key="language_choice",
        on_change=_apply_language,
    )


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
