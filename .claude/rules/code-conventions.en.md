*[Versão em português](code-conventions.md)*

# Code Conventions

> Read by the agent when writing or reviewing code. For the domain model, see
> `CONTEXT.en.md`; for the architecture decisions and their whys, `docs/adr/`.
>
> This project's specific constraints must be defined in the *grill with docs* session
> (skill `grill-with-docs`, log in `docs/grills_logs/`) and recorded in the
> [This project's constraints](#this-projects-constraints) section below.

---

## Language

- **Code** (modules, identifiers, docstrings) in **English**.
- **Documentation** (ADRs, `CONTEXT.md`, README, log) in **Portuguese**.
- The glossary in `CONTEXT.en.md` bridges the domain term (pt-BR) and the identifier in the
  code (English).

---

## Per-language conventions

The rules specific to each language live in separate files, so as not to assume a stack the
project does not use:

- **Python** → [`python-conventions.en.md`](./python-conventions.en.md)
- Other languages: add `rules/<language>-conventions.md` as the project needs (e.g.,
  `typescript-conventions.md`).

---

## Clean Code

- Single-responsibility functions — if the name needs an "and"/"or", split it.
- Descriptive names: no opaque abbreviations (`nd` → `node`, `sz` → `size`).
- Constants in `UPPER_SNAKE_CASE`; variables and functions in `snake_case`; classes in
  `PascalCase`.
- Comments explain *why*, not *what*.
- See also `.claude/rules/karpathy-principles.md` (simplicity first, surgical changes,
  goal-oriented execution).

---

## This project's constraints

> To be filled in during this project's *grill with docs* session. Domain model in
> [`CONTEXT.en.md`](../../CONTEXT.en.md); decisions and whys in [`docs/adr/`](../../docs/adr/).
>
> Examples of what goes here: language/version, core vs. optional dependencies, interface
> type (CLI/web/API), persistence format, reproducibility, folder structure — whatever is
> specific and non-obvious to this project.

<to be filled in>
