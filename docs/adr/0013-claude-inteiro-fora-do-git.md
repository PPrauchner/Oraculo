*[English version](0013-claude-inteiro-fora-do-git.en.md)*

# `.claude/` inteiro fica fora do git

Altera o [ADR-0012](0012-versiona-docs-e-convencoes-ignora-tooling.md). O ADR-0012
versionava `.claude/rules/` para o `CLAUDE.md` não publicar links pendurados. Só que
as convenções ali não são conhecimento do ORÁCULO: são texto genérico de um kit
pessoal de ferramentas, que não é publicado. Com a pasta versionada, qualquer rule
nova que entrasse nela iria a público junto.

**Decidido:** ignorar `.claude/` inteiro e tirar do `CLAUDE.md` a linha que
apontava para `.claude/rules/`. Com isso não sobra link pendurado, que era a
preocupação do ADR-0012.

Continua valendo do ADR-0012: `CLAUDE.md` e `CONTEXT.md` são versionados, e o
critério da #17 segue verificável pela árvore versionada.
