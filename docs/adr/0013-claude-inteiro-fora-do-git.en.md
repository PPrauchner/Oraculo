*[Versão em português](0013-claude-inteiro-fora-do-git.md)*

# The whole `.claude/` stays out of git

Amends [ADR-0012](0012-versiona-docs-e-convencoes-ignora-tooling.en.md). ADR-0012
versioned `.claude/rules/` so that `CLAUDE.md` would not publish dangling links. But
the conventions there are not ORÁCULO knowledge: they are generic text from a
personal toolkit that is not published. With the folder versioned, any new rule
added to it would go public along with it.

**Decided:** ignore the whole `.claude/` and remove the `CLAUDE.md` row that pointed
to `.claude/rules/`. That leaves no dangling link, which was ADR-0012's concern.

Still valid from ADR-0012: `CLAUDE.md` and `CONTEXT.md` are versioned, and the #17
criterion remains verifiable from the versioned tree.
