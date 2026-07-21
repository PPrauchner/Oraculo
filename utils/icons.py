"""
Reusable inline SVG icons.

Home of the decorative icons the screen draws, kept as inline SVG rather than emoji: an
emoji is a glyph the font paints in its own color, while an SVG here inherits the color
of its container (`stroke="currentColor"`), so a single definition follows both the
light and the dark theme without a variant per background (issue #45).

No icon library: the same reasoning that dropped Babel in ADR-0009 — a new dependency in
a tool that audits dependencies would show up in its own self-audit, and it would be
dozens of icons pulled in to use a couple. Six hand-written SVGs are cheaper than that.

Responsibilities:
- Hold each reusable icon as a `currentColor` SVG string.
"""

# The magnifying glass, drawn by the sidebar title and the browser tab. It inherits the
# color of its container via `currentColor`, so it follows the theme without carrying its
# own color.
# Must start with `<svg` and no leading whitespace: Streamlit's favicon detection only
# tolerates a single leading space (`^\s?<svg`), so a leading newline sends `page_icon`
# down the file-path branch and the tab shows nothing. Keep `<svg` flush with the quotes.
SVG_LUPA = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" transform="scale(-1, 1)" transform-origin="center" style="margin-right: 10px; vertical-align: middle;">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    </svg>"""

# The check that marks a finished step in the loading list. Kept on one line so it sits
# inline right after the step label; it inherits the step's color (green, for done) via
# `currentColor`.
SVG_CHECK = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><polyline points="20 6 9 17 4 12"></polyline></svg>'
