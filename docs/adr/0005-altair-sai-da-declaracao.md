# altair sai da Declaração; só-restrição não vira isenção

O `pyproject.toml` declarava `altair<5` e nenhum módulo do projeto importa altair — um
Zumbi pela letra do `CONTEXT.md`. A suspeita era que o `<5` fosse uma restrição deliberada,
segurando uma transitiva do `streamlit` abaixo da 5.x. Não é: `streamlit` aceita
`altair!=5.4.0,!=5.4.1,<7,>=4.0`, e remover a linha muda a resolução em nada — o `uv.lock`
perde exatamente duas linhas (a entrada em `dependencies` e o especificador em
`requires-dist`) e o altair continua em 4.2.2, agora como transitiva pura do `streamlit`.
Declaração removida.

Por que registrar: o caso expõe a **declaração só-restrição** — declarar um pacote sem
importá-lo, só para pinar a versão de uma transitiva. É Zumbi pela definição e falso
positivo na prática, e a saída tentadora era isentá-la da classificação, como fazemos com
as Dependências de Desenvolvimento (ADR-0003). Recusamos: aqui não havia instância real —
o `<5` não prendia nada — e uma isenção assim se aplica sozinha, porque qualquer Zumbi pode
alegar que existe para restringir alguém. Isso esvaziaria a US-03. O conceito entra no
domínio quando aparecer um caso verdadeiro, não por precaução.

Consequência a não confundir com esta decisão: altair 4.2.2 é de janeiro de 2023 e não
sobrevive ao pandas 3 que o projeto resolve — serializar um gráfico nativo do Streamlit
levanta `TypeError: Cannot interpret '<StringDtype(na_value=nan)>' as a data type`. A app
escapa porque desenha com Plotly (`pages/report.py`) e nunca chama `st.*_chart`. Remover a
declaração não corrige nem agrava isso: a versão travada estava no Lock, não na Declaração.
Destravá-la é `uv lock --upgrade-package altair`, decisão de outra ordem.
