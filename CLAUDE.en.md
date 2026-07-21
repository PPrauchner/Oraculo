*[Versão em português](CLAUDE.md)*

# CLAUDE.md — ORÁCULO

Python dependency-auditing tool (Streamlit). It takes a Target Project, crosses what it
**declares** with what it **imports**, queries PyPI and reports Zombies, Ghosts and Outdated
ones.

Academic work (RP III, Marco I) — the [assignment](./docs/Enunciado.en.md) is the contract:
requirements come from there, not from product intuition.

## Read before implementing

| File | What it is |
|---|---|
| [`CONTEXT.en.md`](./CONTEXT.en.md) | **Domain glossary.** Zombie, Ghost, Used Version, Size, Age have an exact definition. Use these terms. |
| [`docs/adr/`](./docs/adr/) | **Why** the non-obvious decisions are the way they are. Read before "fixing" something that looks wrong. |
| [`docs/Enunciado.en.md`](./docs/Enunciado.en.md) | Requirements and user stories (US-01…US-07). |
| [`.claude/rules/`](./.claude/rules/) | Conventions for code, Python and working principles. |

## Stack and commands

Python ≥3.11, managed by **uv**. Streamlit multipage via `st.navigation`.

```bash
uv sync                        # install dependencies
uv run streamlit run main.py   # run the application
uv run pytest                  # run the tests
```

## Architecture

Procedural pipeline (Rule 01 of the assignment: **procedural paradigm** — no domain classes).
`pages/loading.py` orchestrates; `core/` has the steps; nothing in `core/` imports `streamlit`.

```
main.py                 Streamlit navigation
pages/                  UI — home (entry), loading (orchestrates the pipeline), report (US-06/07)
core/ingestion/         open the Target Project and filter Exclusions
core/parsin/            read Declarations/Lock (readers) and extract Root Imports (import_parser)
core/analysis/          classify Zombies, Ghosts, Outdated
core/pypi/              client of the public PyPI API
core/report/            consolidate and export (CSV)
utils/                  constants, sidebar, function registries
utils/display.py        dresses the report data in the screen's language
utils/messages.py       dresses the error code from `core/` in the screen's language
```

**Registries.** `utils/functions.py` exposes the `registrar` decorator and two dictionaries:
`EXTRATORES` (extension → function that opens the file) and `READERS` (filename → parser).
Supporting a new format = writing the function and decorating it; no new `if` in `pages/`.
Careful: the registry only populates if the module is imported — that is why `pages/loading.py`
does `import core.parsin.readers` without apparently using it.

**State.** Passes through `st.session_state` between pages (`archive`, `ignore_folders`,
`all_dependencies`, `zombies`, `ghosts`, `analysis_complete`). A Streamlit rerun re-executes
the whole page top to bottom.

## Invariants

Consequences of the decisions in the ADRs. Violating this is regression, not style:

- **The Lock never defines the audited set**, it only resolves versions (ADR-0002). Reading
  `uv.lock` as a Declaration makes every transitive become a Zombie.
- **A Development Dependency is never a Zombie** (ADR-0003). `ruff`/`mypy` are imported by
  nobody, and `pytest` lives in the Exclusions.
- **An Own Module is never a Ghost.** `core`, `utils` and `pages` belong to the Target Project,
  not to PyPI.
- **Size and Age come from PyPI, not from disk** (ADR-0004) — they must give the same number in
  both ingestion modes (ADR-0001).
- **Import Name ≠ Distribution Name.** Without resolving the Alias, a package becomes a Ghost
  and a Zombie at the same time. `.lower().replace("-","_")` is not enough.
- **Do not invent a Used Version.** With no Lock and no pin, Age/Size are unavailable — report
  the Undetermined (`UNKNOWN`), never assume the PyPI version. It is not to be confused with the
  Not Applicable (`N/A`, the Origin of a Ghost): "we don't know" and "does not apply" are
  different problems, and only the first improves with a Lock.
- **`core/` does not know Streamlit — nor the screen's language.** The return is a **stable
  English code plus the data that describes it** — `("directory_not_found", {"path": ...})` —,
  never a ready-made sentence or emoji (ADR-0010). It holds for the error and for the data: the
  report comes out in bytes and days, not in "1.2 MB" and "30 days". Icon, unit, wording and
  language belong to whoever renders — `utils/messages.py` for errors, `utils/display.py` for
  the report.
- **Identity is not a label.** Category, Status and Origin are compared, not just displayed:
  `dep["status"] == STATUS_OUTDATED` decides the CSV's Outdated column and the Outdated tab.
  Translating the value along with the text breaks the comparisons silently. Identity in English
  in `utils/constants.py`; label via `t()` at render time.

## Known traps

- ORÁCULO **is a valid Target Project** — use it to test. Today it passes its own audit: no
  Ghosts (issue #28) and no Zombies (issue #32). The grill-session log in `docs/grills_logs/`
  describes the old audit, which still failed.
- `tests/integration/test_self_audit.py` guards this state: touching the `pyproject.toml`
  Declaration without touching the imports breaks either the Ghost test or the Zombie test.
  Before declaring a new package, actually import it; when you stop importing it, take it out of
  the Declaration.
- The product name is **ORÁCULO** (Organizador e Rastreador Automático de Código, Uso de
  Libraries e Ocorrências). `Baita Auditor` and `DP-Auditor` are old names; `problema-01` was
  never a product name, only a working folder. Documentation and code already use the new name
  (issues #23, #24, #31) — the old name only survives on purpose in `docs/grills_logs/`, which
  is a point-in-time historical record.
