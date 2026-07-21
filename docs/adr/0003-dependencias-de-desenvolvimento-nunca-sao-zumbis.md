*[English version](0003-dependencias-de-desenvolvimento-nunca-sao-zumbis.en.md)*

# Dependências de Desenvolvimento nunca são Zumbis

Todas as Declarações encontradas são unidas para formar o conjunto auditado — inclusive
`requirements-dev.txt` e `[dependency-groups]`. Isso, sozinho, sabotaria a US-02: o dev
exclui `tests/` (o exemplo que a própria US-02 dá), e então `pytest` — importado só lá
dentro — vira Zumbi. Pior, `ruff` e `mypy` não são importados por ninguém em lugar nenhum,
por serem ferramentas de linha de comando: seriam Zumbis em qualquer configuração.

Por isso os readers preservam a **Origem** de cada pacote, e o que vem de um grupo de
desenvolvimento é isento da classificação Zumbi. Continua entrando no Total e recebendo
Tamanho, Idade e status de Desatualizada — apenas não é cobrado por não ser importado.

Sem esse recorte, quanto mais corretamente o usuário usasse a US-02, mais falsos Zumbis a
US-03 produziria — as duas histórias se anulariam.
