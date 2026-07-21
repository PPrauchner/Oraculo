"""
Resolves the label the user reads in the chosen language.

Responsibilities:
- Load the labels from `locales/<language>.json`.
- Translate a key, falling back to English when it is missing in the requested language.
- Read from the URL (`?lang=`) the language of the current request.

The language lives in the query param, and not in `st.session_state`, for two reasons: it
survives the refresh and the link comes out shareable already translated. For the same reason
no translated label is stored in state — `t` resolves at render time, otherwise
changing the language would show a stale label until the analysis is re-run.
"""

import json
from pathlib import Path

import streamlit as st

LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"

# English is the default: the work has already been graded and the project now serves as a
# portfolio, so the examining board is no longer the default audience (ADR-0009).
DEFAULT_LANGUAGE = "en"

# Name of the query param that carries the language.
LANGUAGE_PARAM = "lang"


def available_languages() -> list[str]:
    """Languages the interface offers, in alphabetical order.

    Returns:
        One code per file in `locales/`. Supporting a new language is adding
        the file — no code changes (ADR-0009).
    """
    return sorted(locale_file.stem for locale_file in LOCALES_DIR.glob("*.json"))


def resolve_language(requested: str | None) -> str:
    """Decides which language the interface speaks.

    Args:
        requested: Requested language — in practice, what came in `?lang=`. `None` when
            the parameter is not in the URL.

    Returns:
        The requested language, if there is a file for it; English in any other case.
        The URL is typable, so an unknown value opens in English instead of taking down
        the screen.
    """
    if requested is not None and requested in available_languages():
        return requested

    return DEFAULT_LANGUAGE


def load_locale(language: str) -> dict[str, str]:
    """Reads the labels of a language.

    Args:
        language: Language code, the file name in `locales/` without extension.

    Returns:
        The labels of that language, or empty if it has no file.
    """
    locale_file = LOCALES_DIR / f"{language}.json"

    if not locale_file.is_file():
        return {}

    return json.loads(locale_file.read_text(encoding="utf-8"))


def translate(key: str, language: str) -> str:
    """Returns the label of a key in the requested language.

    Args:
        key: Label identifier, as it is in `locales/*.json`.
        language: Code of the desired language.

    Returns:
        The label in the requested language; English when the key is missing in it. A key
        missing in English too comes back raw: it is a bug of the caller, and hiding that
        would leave the screen empty without saying why. The parity test prevents the
        first fallback from becoming routine, and the complete English, the second from happening.
    """
    translated = load_locale(language).get(key)

    if translated is not None:
        return translated

    return load_locale(DEFAULT_LANGUAGE).get(key, key)


def current_language() -> str:
    """Language of the current request, read from `?lang=` in the URL."""
    return resolve_language(st.query_params.get(LANGUAGE_PARAM))


def t(key: str) -> str:
    """Translates a key in the language of the current request.

    Args:
        key: Label identifier, as it is in `locales/*.json`.

    Returns:
        The label ready for the screen. Call it at render time, never store the
        result in `st.session_state`: the stored label ages when the
        user changes language.
    """
    return translate(key, current_language())
