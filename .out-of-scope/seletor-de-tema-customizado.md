# Seletor de Tema Customizado

O ORÁCULO não tem — e não vai ter — um botão próprio de alternar tema claro/escuro
na interface. O tema é responsabilidade do mecanismo nativo do Streamlit.

Isto **não** significa que o ORÁCULO não tem tema claro e escuro. Tem: o
`.streamlit/config.toml` define `[theme.light]` e `[theme.dark]` a partir de uma
paleta única, e o menu ⋮ → Settings → Theme alterna entre eles. O que está fora de
escopo é **reimplementar esse controle por conta própria**.

## Por que está fora de escopo

O Streamlit trava a troca de tema em runtime, de propósito:

```python
>>> st.set_option("theme.base", "light")
StreamlitAPIException: theme.base cannot be set on the fly.
Set as command line option, e.g. streamlit run script.py --theme.base,
or in config.toml instead.
```

A opção `theme.base` é marcada `scriptable = False` no template de configuração.
Não é omissão nem bug — é decisão explícita do framework.

Sobram dois contornos, e ambos custam mais do que entregam:

**Contornar pela API privada** (`st._config.set_option`) funciona, mas o config é
global do servidor. A escolha de um visitante mudaria o tema de todos os outros
simultaneamente. E o mecanismo nativo do Streamlit **já é por sessão** — a
preferência do visitante fica no navegador dele. Ou seja, esse contorno troca uma
solução por-sessão correta por uma global: é regressão, não recurso.

**Contornar por CSS injetado por sessão** funciona e é por sessão, mas reabre a
injeção de `unsafe_allow_html` que a issue #39 removeu das páginas, e passa a
brigar com o `config.toml`, que continua sendo a fonte da verdade das cores.
Preço alto por um recurso que já existe nativamente e funciona.

## O que era o problema de verdade

O pedido original não era "o tema não funciona" — era "ninguém acha o botão". O
mecanismo estava certo; faltava **descoberta**. Isso se resolve apontando o
caminho, não reconstruindo o controle.

## Prior requests

- #48 — "Alternar tema pela interface esbarra em theme.base nao-scriptable"
  (decidido em 2026-07-20: manter o nativo, resolver a descoberta)

## Como a descoberta foi resolvida

A barra lateral mostra a legenda `sidebar.theme_hint`, que aponta o caminho do menu
nativo. É legenda e não controle de propósito — uma dica com cara de botão que não
alterna nada seria pior do que não sinalizar. `tests/units/utils/test_theme.py`
guarda que nenhum módulo escreve o tema, para esta decisão não ser refeita sem querer.
