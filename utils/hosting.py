"""
Tells whether the ORÁCULO is running published, and not on the user's machine.

Directory ingestion (ADR-0001) assumes Streamlit runs on the dev's machine, so a
typed path resolves there. Published, the same path would resolve on the server and
expose its file system to any visitor — so the hosted mode turns directory ingestion
off (ADR-0014).

The decision is configuration, read from the environment only: on Streamlit
Community Cloud a root key of the *Secrets* reaches the process as an environment
variable, so `st.secrets` is never read and the app does not depend on
`.streamlit/secrets.toml` existing. It lives outside `core/`, which knows nothing
about where it runs.

Responsibilities:
- Answer "are we hosted?" from `ORACULO_HOSTED`.
"""

import os

# Name of the environment variable that turns the hosted mode on.
HOSTED_VARIABLE = "ORACULO_HOSTED"

# Values that turn it on, compared without case. Anything else — absent, empty,
# "false", "0" or a typo — leaves the local behavior untouched.
TRUTHY_VALUES = frozenset({"true", "1"})


def is_hosted() -> bool:
    """Whether the hosted mode is on.

    Returns:
        `True` when `ORACULO_HOSTED` is `true` or `1`, ignoring case and surrounding
        whitespace; `False` in any other case, the variable's absence included.
    """
    return os.environ.get(HOSTED_VARIABLE, "").strip().lower() in TRUTHY_VALUES
