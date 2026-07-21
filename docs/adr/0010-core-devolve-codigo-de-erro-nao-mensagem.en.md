*[Versão em português](0010-core-devolve-codigo-de-erro-nao-mensagem.md)*

# `core/` returns an error code, not a ready-made message

The invariant says `core/` does not know Streamlit, and to the letter it was respected: no
`core/` module imports `streamlit`. But `core/ingestion/` returned things like:

```python
return False, "❌ O Projeto-Alvo não foi processado corretamente."
return None, f"❌ Caminho não encontrado: {directory}"
```

`core/` did not call `st.error()`, but it decided **how the error appears** (the `❌`) and **in
which language it speaks** (Portuguese). There are twelve messages like this. The coupling was
not in the import; it was in the string. This only became visible when the product came to have
two languages: an already-formatted message arrives in `pages/` as opaque text, and there is
nothing left to translate.

**`core/` returns a stable error code and the data that describes it; `pages/` chooses icon,
formatting and language at render time.**

```python
return None, ("directory_not_found", {"path": directory})
```

The code is an English identifier, like the rest of `core/`, and does not change with the
screen's language — the same logic that fixed the CSV as a contract (ADR-0008). The icon stops
being a character embedded in the text and becomes a presentation decision, resolved with SVG
in `pages/`. Each message comes to exist once per language in `locales/` (ADR-0009), instead
of once, in Portuguese, in the middle of the ingestion logic.

The cost is churn: the signature of the ingestion functions changes and the tests that matched
against the message text come to match against the code. In exchange, those tests get better —
matching against `"directory_not_found"` does not break when someone rewrites the sentence.

Rejected: **typed exceptions** (`raise DirectoryNotFound(path)`). It is more idiomatic in pure
Python and carries the same data, but it swaps the return style `core/ingestion/` already uses
consistently for `try/except` scattered across `pages/` — a larger refactor, to solve a
problem the error code solves without changing the flow's shape.

Rejected: **just removing the emoji**, keeping the message in Portuguese. It meets the literal
request and meets none of its reasons: every error message would stay stuck in Portuguese in an
app whose default has become English, and `core/` would keep deciding presentation.
