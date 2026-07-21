*[Versão em português](0009-locales-em-json-sem-biblioteca-de-i18n.md)*

# Locales in JSON, no i18n library

ORÁCULO comes to offer the interface in Portuguese and English. The canonical path for that is
`gettext`/Babel: automatic extraction, `.po` files, pluralisation and context — solved for
decades and known by any reviewer.

**The translation lives in `locales/en.json` and `locales/pt.json`, resolved by a function of
our own, with no new dependency.** These are about 60 labels, with no pluralisation and no
complex interpolation; what Babel solves beyond that is a problem this product does not have.

The decisive reason is another, and it is specific to this project: **ORÁCULO is a tool that
denounces dependencies a project carries without needing them, and it audits itself in
`tests/integration/test_self_audit.py`.** Adding Babel — megabytes and a `.po` → `.mo`
compilation step — to translate 60 strings would put into the very Declaration exactly the
kind of weight the product exists to point at. The tool has to withstand its own criterion.

The format is JSON, and not a `dict` in a Python module, for coherence with the
`EXTRATORES`/`READERS` registries: there, supporting a new file format is writing a function
and decorating it, with no new `if` in `pages/`. Here, supporting a new language is adding a
file, without touching code. The same idea, applied twice.

What the JSON loses relative to the Python module is the difficulty of publishing half a
translation — a `dict` is at least visibly asymmetric next to the other. That is bought back
by two guarantees: **a missing key falls back to English** (the screen is bilingual for an
instant, never broken nor full of raw identifiers), and **a test requires that the two files
have exactly the same set of keys**, which is what turns "I forgot to translate" into a build
failure instead of a production discovery.

The default is English, because the project now serves as a portfolio and the default audience
has stopped being the examining board. The choice persists in `?lang=`, so a Portuguese link
is still shareable. The documentation stays in Portuguese (workspace convention); `.en.md`
versions are left for later.

Orthogonal and already decided: the selector **does not reach the CSV**, which is a fixed
English contract (ADR-0008). Switching the language changes the screen and nothing in the
exported file.
