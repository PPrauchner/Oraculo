*[English version](0002-declaracao-define-o-conjunto-lock-define-a-versao.en.md)*

# Declaração define o conjunto, Lock define a versão

A Declaração (`pyproject.toml`, `requirements.txt`) diz **quais** pacotes são diretos mas
raramente pina versão (`pandas>=3.0.1`); o Lock (`uv.lock`, `poetry.lock`) diz **em que
versão** tudo resolveu, mas lista também centenas de transitivas. Cada arquivo responde
metade da pergunta, então lemos os dois: a Declaração forma o conjunto auditado
(Zumbis/Fantasmas) e o Lock, quando existe, resolve a Versão Usada de cada item do
conjunto (Idade/Tamanho/Desatualizada).

Por que registrar: é tentador simplificar para "leia só o Lock, ele tem nome e versão de
tudo". Era o que `_find_dependency_file` fazia na prática, ao devolver o primeiro arquivo
que casasse — num projeto uv isso lia o `uv.lock` e reportava toda transitiva como Zumbi,
porque nenhuma delas é importada pelo código. O Lock **não** é fonte de conjunto.

Consequência: sem Lock, a Versão Usada de uma dependência não pinada é desconhecida —
Idade e Tamanho ficam indisponíveis para ela. Preferimos isso a inventar uma versão. Em
particular, o comportamento atual de `outdated_analizer.py`, que copia a versão do PyPI
para `Versão Atual` quando não há versão declarada e marca "Atualizado", está errado por
essa régua: reporta como atualizado algo cuja versão não se conhece.
