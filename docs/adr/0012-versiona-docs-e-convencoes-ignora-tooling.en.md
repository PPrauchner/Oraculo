*[Versão em português](0012-versiona-docs-e-convencoes-ignora-tooling.md)*

# Documentation and conventions are versioned; the `.claude/` tooling config stays out

The `.gitignore` that came in PR #20 ignored `CLAUDE.md` and `.claude/` entirely — only
`CONTEXT.md` ended up tracked. In a project that is now a portfolio piece, whoever opens the
repository is a recruiter or a technical reviewer, and the **project documentation must be
legible from the versioned tree**, not from the disk of whoever wrote it. The gap surfaced in
the #20 review: US #17's DoD — "the `CLAUDE.md` reflects the command that actually works" — is
not verifiable when `CLAUDE.md` is not in the repository.

**Decided:** version `CLAUDE.md`, `CONTEXT.md` and `.claude/rules/`; keep the rest of
`.claude/` ignored. `CLAUDE.md` is pure onboarding (what ORÁCULO is, stack, architecture,
invariants, traps) and serves the external reader from start to finish — there is no tooling
content to separate from it. `.claude/rules/` enters because `CLAUDE.md` **references** those
conventions as shared; leaving them out would publish a `CLAUDE.md` with dangling links.
`CONTEXT.md` was already tracked — the decision merely formalises it.

The `.gitignore` now lists `.claude/*` with `!.claude/rules/`: it ignores the directory's
contents and reopens only the conventions. That way `.claude/settings.local.json` (local,
personal permissions) and `.claude/current-issue` (ephemeral session state) stay out **by
construction**, with no rule of their own.

Rejected: **versioning nothing from `.claude/`**. It is the simplest, but it leaves
`CLAUDE.md`'s references to `.claude/rules/` dangling for whoever reads the repository.

Rejected: **versioning the whole `.claude/`** (commands, skills, hooks, scripts). The skills
are mostly generic upstream copies of Claude's, not specific to the project, and dumping them
into the tree becomes noise for the external reader — the opposite of the goal. The workflow
machinery can enter later, in a concrete case, if some command becomes genuine documentation of
the team's process.

Consequence: US #17's criterion becomes verifiable from the versioned tree — the commands in
`CLAUDE.md` (`uv sync`, `uv run streamlit run main.py`, `uv run pytest`) now live in the
repository and can be checked against it.
