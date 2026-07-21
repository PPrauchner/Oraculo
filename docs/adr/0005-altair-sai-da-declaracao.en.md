*[Versão em português](0005-altair-sai-da-declaracao.md)*

# altair leaves the Declaration; constraint-only is no exemption

The `pyproject.toml` declared `altair<5` and no module of the project imports altair — a
Zombie by the letter of `CONTEXT.md`. The suspicion was that the `<5` was a deliberate
constraint, holding a `streamlit` transitive below 5.x. It is not: `streamlit` accepts
`altair!=5.4.0,!=5.4.1,<7,>=4.0`, and removing the line changes resolution by nothing —
`uv.lock` loses exactly two lines (the entry in `dependencies` and the specifier in
`requires-dist`) and altair stays at 4.2.2, now as a pure `streamlit` transitive. Declaration
removed.

Why record it: the case exposes the **constraint-only declaration** — declaring a package
without importing it, only to pin a transitive's version. It is a Zombie by definition and a
false positive in practice, and the tempting way out was to exempt it from classification, as
we do with Development Dependencies (ADR-0003). We refused: here there was no real instance —
the `<5` held nothing back — and an exemption like that applies itself, because any Zombie
could claim it exists to constrain someone. That would hollow out US-03. The concept enters
the domain when a true case appears, not as a precaution.

Consequence not to confuse with this decision: altair 4.2.2 is from January 2023 and does not
survive the pandas 3 the project resolves — serialising a native Streamlit chart raises
`TypeError: Cannot interpret '<StringDtype(na_value=nan)>' as a data type`. The app escapes
because it draws with Plotly (`pages/report.py`) and never calls `st.*_chart`. Removing the
declaration neither fixes nor worsens this: the pinned version was in the Lock, not in the
Declaration. Unpinning it is `uv lock --upgrade-package altair`, a decision of another order.
