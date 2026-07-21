"""
Vertical rhythm and reading width of the application, in a single place.

Streamlit does not expose the block container spacing declaratively —
`st.set_page_config(layout=...)` chooses between narrow and wide, and nothing more. That
is why there is a stylesheet here, which issue #39 banned from the pages. The difference
is structural, not one of intent:

- **Single place**: declared here and applied once in `main.py`, for the whole
  application — not one block per page, which was the removed defect.
- **Layout only**: spacing, width and centering. No color, no hex,
  no typeface family; the color still comes entirely from
  `.streamlit/config.toml`, which remains the source of truth.
- **No fragile selector**: `.block-container` is a public Streamlit class;
  `data-testid` is an internal detail, which changes from version to version without warning.

Responsibilities:
- Declare the application's layout stylesheet.
- Apply it once per page execution.
"""

import streamlit as st

# The Streamlit default reserves ~6rem above the first element, space meant for
# the floating toolbar. On a laptop screen that pushes the controls
# below the fold before the user has done anything.
CONTENT_TOP_PADDING = "3rem"

# `layout="wide"` removes the width cap, and without a cap the body follows the monitor: on an
# ultrawide the two columns of the initial screen drift apart to the point where the eye loses the
# line between the label and the field. The value is fixed on purpose — as a percentage it
# would grow again with the screen, which is the defect, not the fix.
READING_MAX_WIDTH = "1100px"

LAYOUT_STYLESHEET = f"""<style>
.block-container {{
    padding-top: {CONTENT_TOP_PADDING};
    max-width: {READING_MAX_WIDTH};
    margin-left: auto;
    margin-right: auto;
}}
</style>"""


def apply_layout() -> None:
    """Applies the application's vertical rhythm and reading width.

    Call once, at the entry point, before the page runs: the stylesheet applies to
    all pages at once, and repeating the call page by page would be exactly
    the scattered CSS that issue #39 removed.
    """
    st.html(LAYOUT_STYLESHEET)
