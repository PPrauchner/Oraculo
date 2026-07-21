*[Versão em português](CONTEXT.md)*

# ORÁCULO

**ORÁCULO** — *Organizador e Rastreador Automático de Código, Uso de Libraries e
Ocorrências* (Portuguese for "automatic organiser and tracker of code, library usage and
occurrences").

A dependency-auditing tool for Python projects. It crosses what a project **declares** it
depends on with what its code **actually imports**, and confronts both against PyPI to
assess dependency health.

## Language

### What gets analysed

**Target Project**:
The Python project whose dependencies are being audited. Never ORÁCULO itself.
_Avoid_: project, input, upload

**Declaration**:
The file where the Target Project states which packages it depends on (`pyproject.toml`,
`requirements.txt`, `requirements-dev.txt`, `environment.yml`). Defines **which** packages
are direct, not at which version. A Target Project may have several, and all of them count.
_Avoid_: manifest, config, dependency file

**Origin**:
Which Declaration — and which section of it — a package came from. It is what separates a
Production Dependency from a Development Dependency.
_Avoid_: source, group, scope

**Lock**:
The file that records the exact version of each package that was actually resolved
(`uv.lock`, `poetry.lock`). Defines **at which version**, not which ones are direct.
_Avoid_: lockfile, freeze

**Exclusion**:
A **folder name** the user marked to stay out of the audit (e.g. `tests`, `docs`), matching
at any depth: marking `tests` excludes `tests/` and `src/tests/` (ADR-0007). Code inside an
Exclusion generates no imports and no declarations. Two folders with the same name at
different levels are indistinguishable — the price of no folder offered in the UI failing to
exclude.
_Avoid_: ignore, filter, blacklist, path

### A package's identity

**Distribution Name**:
The name a package is published under on PyPI and written under in the Declaration (e.g.
`PyYAML`, `scikit-learn`).
_Avoid_: package name, real name

**Import Name**:
The name a package is imported by in code (e.g. `yaml`, `sklearn`). Not necessarily equal to
the Distribution Name.
_Avoid_: module, module name

**Root Import**:
The first segment of an import, which is what identifies the package (`django.core.cache` →
`django`). Relative imports, stdlib modules and Own Modules are not Root Imports.
_Avoid_: import, used dependency

**Own Module**:
A package defined by the Target Project itself (e.g. `core`, `utils`), recognisable by
existing as a top-level folder with `__init__.py`. It is nobody's dependency and is never a
Ghost.
_Avoid_: local module, internal, first-party

**Import Alias**:
The case where the Import Name differs from the Distribution Name (`yaml` ↔ `PyYAML`).
Without resolving it, one and the same package becomes a Ghost and a Zombie at once.
_Avoid_: mapping, translation, lookup table

### Audit categories

**Declared Dependency**:
A package that appears in some Declaration of the Target Project.
_Avoid_: installed dependency, requirement

**Production Dependency**:
A Declared Dependency the main code needs to run. Origin: `[project].dependencies` or
`requirements.txt`.
_Avoid_: real dependency, runtime, main

**Development Dependency**:
A Declared Dependency that serves work *on* the code, not its execution. Origin:
`requirements-dev.txt`, `[dependency-groups]` or `[project.optional-dependencies]`. Never a
Zombie: many (ruff, mypy) are imported by nobody, and the rest live precisely in the
Exclusions.
_Avoid_: dev dependency, optional dependency, extra

**Zombie Dependency**:
A Production Dependency whose Distribution Name matches no Root Import found outside the
Exclusions. Paid for, but unused.
_Avoid_: dead dependency, orphan, unused

**Ghost Dependency**:
A Root Import that matches no Declared Dependency. It works on the dev's machine by riding
along as a transitive, and breaks in another environment.
_Avoid_: implicit dependency, hidden, missing

**Outdated Dependency**:
A dependency whose Used Version is older than the latest version published on PyPI.
_Avoid_: obsolete, old, stale

**Category**:
How a dependency is classified in the report and the export: Zombie, Ghost or Healthy. It is
exclusive — each dependency comes out in exactly one row. Outdated is **not** a Category: it
is a column of its own, because a dependency can be a Zombie *and* Outdated at the same time.
_Avoid_: type, class, status

**Healthy**:
The Category of a dependency that is neither a Zombie nor a Ghost. It only says the
dependency is declared and used — **not** that it is up to date: a row can come out
`Category=Healthy` with `Outdated=Yes`. Not to be confused with the Health Index, which is
stricter and also discounts the Outdated ones.
_Avoid_: OK, too healthy, up to date

### Metrics

**Used Version**:
The version of a package the Target Project actually runs. It comes from the Lock when one
exists; an unpinned Declaration (`>=3.0.1`) does not determine a Used Version on its own.
_Avoid_: current version, declared version, installed version

**Size**:
The bytes of the artifact (wheel; sdist when there is no wheel) of the Used Version, as
published on PyPI. It is not on-disk size and does not include transitives.
_Avoid_: weight, space, on-disk size

**Age**:
Time between the Used Version's release date on PyPI and today. It measures how long the
Target Project has been sitting on that version — not the package's age.
_Avoid_: lifetime, seniority, lag

**Health Index**:
The proportion of Declared Dependencies that are neither Zombies, Ghosts nor Outdated.
Stricter than the Healthy Category, which ignores Outdated.
_Avoid_: score, grade, percentage

### Absence of a value

Two different absences that the report must not confuse: one is a limit of what is known, the
other is a property of what was audited.

**Undetermined**:
ORÁCULO has no way to know the value. This is the case of the Used Version with no Lock and
no pin — and, in consequence, of the Size and Age that depend on it. A Lock would resolve it.
_Avoid_: empty, null, zero, unknown-to-PyPI

**Not Applicable**:
The value does not exist for that dependency, by definition. This is the case of the Origin
of a Ghost: it comes from no Declaration, so there is no section for it to have come from. No
extra file would fill it in.
_Avoid_: unavailable, missing, no data

## Exported-data vocabulary

The CSV is a stable, English contract and does not follow the screen's language (ADR-0008).
These are the only values it emits — translating for display is the responsibility of
`utils/display.py`, and the translation never reaches the file:

| Column | Values |
|---|---|
| `Category` | `Zombie` · `Ghost` · `Healthy` |
| `Origin` | `Production` · `Development` · `N/A` |
| `Status` | `Outdated` · `Up to date` · `Unknown` · `Invalid version` |
| `Outdated` | `Yes` · `No` |
| absence | `Unknown` (Undetermined) · `N/A` (Not Applicable) |

`Status` is not a CSV column: it decides the `Outdated` column and shows up in the on-screen
table. It is here because its values are stable identity for the same reason as the others'
— they are compared, not just displayed.

Three vocabularies coexist, kept apart on purpose so that touching one does not reach the
others by accident: the **internal key** (`used_version`, snake_case), the **CSV header**
(`Used Version`, fixed in English, in `CSV_HEADER`) and the **screen label** (`Versão
Usada` / `Used Version`, in `locales/`). The glossary above bridges to the domain term in
Portuguese.
