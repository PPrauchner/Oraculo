"""
Translates the error code `core/` returns into the sentence the user reads.

Responsibilities:
- Name the locale key of an error code (`error_key`).
- Compose the final sentence with the error's parameters (`format_error`).

`core/` detects the problem and names it in English; the wording, the language and the icon are
a decision of whoever renders (ADR-0010). The text lives in `locales/*.json`, together with the
rest of the screen (ADR-0009): there is a single translation path, so the language selector
reaches the error as it reaches any other label. It stays in `utils/` — and not inside
a page — because `home.py` and `loading.py` display the same errors.
"""

from core.ingestion.source import IngestionError
from utils.i18n import t

# Namespace of the error codes within the locale. Without it, a code coming from `core/`
# could collide with the key of a screen label.
ERROR_KEY_PREFIX = "error."


def error_key(code: str) -> str:
    """Locale key corresponding to an error code from `core/`.

    Args:
        code: Stable English code, as `core/ingestion/` returns it.

    Returns:
        The key to look up in `locales/*.json`.
    """
    return f"{ERROR_KEY_PREFIX}{code}"


def format_error(error: IngestionError) -> str:
    """Composes the sentence of an error returned by `core/`, in the screen language.

    Args:
        error: (code, parameters) pair as `core/ingestion/` returns it.

    Returns:
        The sentence to display. An unknown code comes back raw and a missing parameter leaves
        the placeholder intact: a translation error cannot hide the error the
        user needs to see.
    """
    code, params = error
    key = error_key(code)
    template = t(key)

    # `t` returns the key itself when it is missing in all languages. Here that
    # means a code with no translation — and what the user then sees is the code, which at
    # least is searchable, never the locale identifier, which says nothing.
    if template == key:
        return code

    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template
