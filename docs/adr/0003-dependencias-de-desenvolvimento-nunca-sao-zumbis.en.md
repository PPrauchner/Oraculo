*[Versão em português](0003-dependencias-de-desenvolvimento-nunca-sao-zumbis.md)*

# Development Dependencies are never Zombies

All Declarations found are unioned to form the audited set — including `requirements-dev.txt`
and `[dependency-groups]`. That alone would sabotage US-02: the dev excludes `tests/` (the
very example US-02 gives), and then `pytest` — imported only in there — becomes a Zombie.
Worse, `ruff` and `mypy` are imported by nobody anywhere, being command-line tools: they would
be Zombies in any configuration.

That is why the readers preserve each package's **Origin**, and whatever comes from a
development group is exempt from the Zombie classification. It still enters the Total and still
receives Size, Age and Outdated status — it is simply not charged for not being imported.

Without this carve-out, the more correctly the user followed US-02, the more false Zombies
US-03 would produce — the two stories would cancel each other out.
