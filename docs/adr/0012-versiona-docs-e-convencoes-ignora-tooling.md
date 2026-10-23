*[English version](0012-versiona-docs-e-convencoes-ignora-tooling.en.md)*

> **Alterado pelo [ADR-0013](0013-claude-inteiro-fora-do-git.md):** `.claude/rules/` deixa
> de ser versionado. O resto desta decisão continua valendo.

# Documentação e convenções versionam; a config de tooling do `.claude/` fica de fora

O `.gitignore` que veio no PR #20 excluía `CLAUDE.md` e `.claude/` inteiros — só o
`CONTEXT.md` acabou rastreado. Num projeto que hoje é peça de portfólio, quem abre o
repositório é recrutador ou revisor técnico, e a **documentação de projeto precisa ser
legível a partir da árvore versionada**, não do disco de quem escreveu. A lacuna apareceu na
revisão do #20: o DoD da #17 — "o `CLAUDE.md` reflete o comando que de fato funciona" — não é
verificável quando o `CLAUDE.md` não está no repositório.

**Decidido:** versionar `CLAUDE.md`, `CONTEXT.md` e `.claude/rules/`; manter o resto do
`.claude/` ignorado. `CLAUDE.md` é onboarding puro (o que é o ORÁCULO, stack, arquitetura,
invariantes, armadilhas) e serve ao leitor externo do começo ao fim — não há conteúdo de
tooling a separar dele. `.claude/rules/` entra porque o `CLAUDE.md` **referencia** essas
convenções como compartilhadas; deixá-las de fora publicaria um `CLAUDE.md` com links
pendurados. `CONTEXT.md` já estava rastreado — a decisão apenas o formaliza.

O `.gitignore` passa a listar `.claude/*` com `!.claude/rules/`: ignora o conteúdo do
diretório e reabre só as convenções. Assim `.claude/settings.local.json` (permissões locais,
pessoal) e `.claude/current-issue` (estado efêmero da sessão) continuam fora **por
construção**, sem precisar de regra própria.

Rejeitado: **versionar nada do `.claude/`**. É o mais simples, mas deixa as referências do
`CLAUDE.md` a `.claude/rules/` penduradas para quem lê o repositório.

Rejeitado: **versionar o `.claude/` inteiro** (commands, skills, hooks, scripts). As skills
são em maioria cópias upstream genéricas do Claude, não são específicas do projeto, e
despejá-las na árvore vira ruído para o leitor externo — o oposto da meta. O maquinário de
workflow pode entrar depois, num caso concreto, se algum comando virar documentação genuína do
processo do time.

Consequência: o critério da #17 passa a ser verificável pela árvore versionada — os comandos
do `CLAUDE.md` (`uv sync`, `uv run streamlit run main.py`, `uv run pytest`) agora vivem no
repositório e podem ser conferidos contra ele.
