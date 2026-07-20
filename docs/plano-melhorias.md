# Plano de Melhorias — ORÁCULO

Escopo fechado na sessão de *grill with docs* de 19/07/2026. Decisões não-óbvias estão nos
ADRs [0008](./adr/0008-o-csv-e-contrato-a-lingua-e-so-da-tela.md),
[0009](./adr/0009-locales-em-json-sem-biblioteca-de-i18n.md),
[0010](./adr/0010-core-devolve-codigo-de-erro-nao-mensagem.md) e
[0011](./adr/0011-dependencia-e-typeddict-nao-classe-de-dominio.md); o glossário atualizado
está em [`CONTEXT.md`](../CONTEXT.md).

Contexto que mudou o público-alvo: o trabalho já foi avaliado. O ORÁCULO agora serve de
**portfólio**, o que move o padrão da interface para inglês e torna o histórico de commits
parte da amostra de trabalho.

**Linha de base:** 200 testes verdes em 0.74s. Toda fatia termina com esse número intacto.

---

## A descoberta que organiza o resto

Três dos seis pedidos pareciam independentes e são o mesmo defeito: **valor de apresentação
usado como dado**.

| Onde | O que | Sintoma |
|---|---|---|
| `export.py:34` | cabeçalho do CSV = chaves do dict | trocar a língua corromperia a série temporal da US-07 |
| `report.py:21-33` | rótulo em PT = chave de `report_dict` | trocar a língua quebraria com `KeyError` |
| `constants.py:14` | `"OK ✅"` = chave de `MAPA_CORES_STATUS` | tirar o emoji quebraria a cor do gráfico |
| `home.py:29-30` | `"📦 Upload de archive"` = valor de controle | emoji e língua governando fluxo |
| `core/ingestion/*` | 12 mensagens PT com `❌` | erro intraduzível; `core/` decidindo aparência |

Por isso "trocar os emojis", "traduzir o código" e "adicionar seletor de língua" não são três
tarefas — são a mesma refatoração vista de três ângulos. As fatias abaixo seguem essa ordem.

---

## Fatia 1 — Performance

**Diagnóstico medido** (ORÁCULO auditando a si mesmo, 6 dependências):

| Etapa | Tempo |
|---|---|
| `collect_declarations` | 7 ms |
| `build_lock_version_map` | 22 ms |
| `parse_imports_with_filter` | 33 ms |
| zumbis + fantasmas | ~0 ms |
| **trabalho local** | **62 ms** |
| PyPI (1 request medido) | 395 ms, paralelo em 32 threads |
| **`time.sleep()` em `loading.py`** | **4.500 ms** |

Cerca de **90% da espera é artificial**. As requisições ao PyPI já são paralelas
(`ThreadPoolExecutor(max_workers=32)`) e `.venv` já é corretamente excluído por
`NON_PROJECT_FOLDERS` — não há problema de performance real além do atraso encenado.

- Remover os cinco `time.sleep()` de `pages/loading.py`.
- O progresso passa a ser dirigido pelo trabalho real. **Sem tempo mínimo de exibição**:
  projeto pequeno pisca (a ferramenta *é* rápida, e esconder isso é mentir), projeto grande
  ganha feedback de verdade. Deixar um comentário dizendo isso, para ninguém "consertar o
  flicker" reintroduzindo o sleep.
- `requests.Session` compartilhada em `pypi_client.py`, para reaproveitar conexão e handshake
  TLS entre as threads. Irrelevante para 6 pacotes, relevante para 100+.

**Fora de escopo:** cache de respostas do PyPI. Levanta invalidação (a "versão mais recente"
muda, e um cache velho faz o relatório mentir sobre Desatualizada) para beneficiar só quem
reaudita o mesmo projeto.

**Verificar:** 200 testes verdes; auditoria completa do próprio ORÁCULO em bem menos de 1s.

---

## Fatia 2 — Chaves e valores para inglês

A maior fatia mecânica: **383 ocorrências em 25 arquivos**, ~290 delas em testes. Precisa ir
sozinha num commit — misturada, envenena o diff de todas as outras.

- Chaves: `Pacote` → `package`, `Versão Usada` → `used_version`, `Versão PyPI` →
  `pypi_version`, `Status` → `status`, `Tamanho` → `size`, `Idade` → `age`, `Categoria` →
  `category`, `Origem` → `origin`.
- Valores emitidos por `core/` também vão para inglês (ADR-0008): `Zombie`, `Ghost`,
  `Healthy`, `Production`, `Development`, `Outdated`, `Up to date`, `Invalid version`,
  `Yes`/`No`.
- Os dois sentinelas de ausência ficam **distintos** e ganham nomes que se explicam
  (`CONTEXT.md` → *Ausência de valor*): `Unknown` para o Indeterminado (Versão Usada sem Lock
  nem pin) e `N/A` para o Não Aplicável (Origem de um Fantasma). Não colapsar: "não sabemos" e
  "não se aplica" são problemas diferentes no relatório.
- Introduzir `Dependency(TypedDict)` (ADR-0011) — em runtime segue `dict` puro, paradigma
  procedural intacto; serve para o verificador pegar a chave errada que uma renomeação desse
  tamanho quase certamente produz.
- Docstrings e comentários de `core/` e `utils/` para inglês, conforme
  `.claude/rules/code-conventions.md`. Documentação de projeto (ADRs, `CONTEXT.md`) **continua
  em português**.

**Verificar:** 200 testes verdes antes e depois; CSV exportado com cabeçalho e células 100% em
inglês; nenhuma chave em português sobrando (`grep`).

---

## Fatia 3 — `core/` devolve código de erro

Implementa o [ADR-0010](./adr/0010-core-devolve-codigo-de-erro-nao-mensagem.md). Pré-requisito
do i18n: enquanto `core/` devolver frase pronta em português, nenhuma mensagem de erro é
traduzível.

- As 12 mensagens de `core/ingestion/filter.py` e `core/ingestion/source.py` passam a
  `(código, parâmetros)` — ex.: `("directory_not_found", {"path": directory})`.
- `pages/` escolhe ícone, formatação e língua na renderização.
- Testes que casavam contra o texto passam a casar contra o código — ficam melhores, param de
  quebrar quando alguém reescreve a frase.

**Verificar:** nenhum literal de mensagem de usuário em `core/`; nenhum emoji em `core/`.

---

## Fatia 4 — i18n e explicações

Implementa o [ADR-0009](./adr/0009-locales-em-json-sem-biblioteca-de-i18n.md).

- `locales/en.json` e `locales/pt.json`, resolvidos por função própria. **Sem Babel/gettext** —
  o ORÁCULO se audita a si mesmo, e não pode carregar megabytes para traduzir ~60 strings.
- Padrão **inglês**; escolha persiste em `?lang=`; seletor na sidebar.
- Chave ausente **cai para o inglês** (tela bilingue por um instante, nunca quebrada nem com
  identificador cru vazando).
- **Teste de paridade**: `en.json` e `pt.json` com exatamente o mesmo conjunto de chaves. É o
  que transforma "esqueci de traduzir" em falha de build.
- Tradução acontece **na renderização**, nunca gravada em `session_state` — senão trocar a
  língua mostra rótulo velho até reexecutar a análise.
- Corrigir `CATEGORY_NAMES`: `report_dict` passa a ser chaveado por chave estável
  (`"zombies"`), com o rótulo buscado na hora de exibir.
- Corrigir `UPLOAD_MODE`/`DIRECTORY_MODE`: valor de controle estável, rótulo traduzido.
- **Explicações das categorias**: `help=` nas métricas e abas, com gloss curto voltado ao
  usuário — deliberadamente distinto da definição formal do `CONTEXT.md`, que é para quem
  desenvolve. Cobrir Zumbi, Fantasma, Saudável, Desatualizada, e os dois sentinelas de ausência.
- Remover a dica obsoleta da sidebar ("Ignore pastas de ambiente virtual para acelerar"):
  `NON_PROJECT_FOLDERS` já faz isso automaticamente, então o texto ensina um passo inútil.

> **Risco aceito:** o gloss da UI pode divergir do `CONTEXT.md` com o tempo (não há teste
> amarrando os textos). Mitigação por disciplina: mudou regra de análise, mexe no gloss no
> mesmo commit. Atenção especial ao ADR-0003 — "Dependência de Desenvolvimento nunca é Zumbi"
> é uma exceção que um gloss ingênuo omite e assim mente.

**Verificar:** paridade de chaves passa; app abre em inglês; `?lang=pt` traduz tudo, inclusive
erros; CSV **idêntico** nas duas línguas (a garantia central do ADR-0008).

---

## Fatia 5 — Tema claro e escuro

**Descoberta que barateou esta fatia:** o projeto roda Streamlit **1.56**, que expõe
declarativamente quase tudo que exigiria CSS frágil acoplado a `data-testid`.

- `.streamlit/config.toml` com `[theme.light]` e `[theme.dark]` — hoje **não existe nenhum
  arquivo de tema**; há três blobs de CSS ad-hoc brigando entre si e com o Streamlit.
- Unificar a paleta: existem **três azuis diferentes** — `constants.BLUE` (`#3498DB`), botão em
  `home.py` (`#1a73e8`), etapa ativa em `loading.py` (`#5dade2`).
- As categorias mapeiam nos tokens semânticos que o Streamlit já traz, e que se adaptam sozinhos
  aos dois fundos: **Zumbi → `violetColor`, Fantasma → `redColor`, Desatualizada → `blueColor`,
  Saudável → `greenColor`**. `MAPA_CORES_STATUS` deixa de ser quatro hexes fixos.
- `theme.chartCategoricalColors` alimenta o donut do Plotly; conferir o contraste do gráfico nos
  dois modos.
- Polimento por config (`baseRadius`, `buttonRadius`, `showWidgetBorder`, `headingFont`,
  `metricValueFontSize`) antes de recorrer a CSS. CSS custom só para o que a config não
  expressa — cada `!important` é uma quebra futura em upgrade do Streamlit.
- Remover `visual_css()` de `home.py` e o bloco `<style>` de `loading.py`.

**Defeitos concretos a corrigir no loader** (`pages/loading.py`):
- `min-height: 150vh` deixa a tela de carregamento 1,5× mais alta que a viewport, forçando
  scrollbar durante a análise;
- `border-radius: 70%` faz o "ring" não ser redondo;
- `_render_progress_steps` emite **dois `</div>` a mais**, somados a um `</div>` solto em
  `_render_loading_ui`.

**Verificar:** app legível e coerente nos dois modos; nenhum hex hardcoded fora da paleta única;
HTML do loader balanceado; sem scroll durante o carregamento.

---

## Fatia 6 — Ícones SVG

- Módulo dedicado (ex.: `utils/icons.py`) com os SVGs reutilizáveis, importados onde
  necessário. Estende o padrão que `SVG_LUPA` já estabeleceu em `constants.py`.
- SVGs herdam `currentColor`, para funcionarem nos dois temas sem duplicação.
- Substituir os decorativos: 🔍 (`main.py`), 🚀 📦 📂 (`home.py`), 📊 📋 📥 (`report.py`),
  ✅ (`loading.py`).
- **Sem biblioteca de ícones** — mesmo argumento que derrubou o Babel: uma dependência nova
  numa ferramenta que audita dependências aparece na própria auto-auditoria.
- Os emojis que eram *dado* (`"OK ✅"`, `"📦 Upload de archive"`) já morreram nas fatias 2 e 4;
  aqui sobram só os decorativos.

**Verificar:** zero emojis no código (`grep`); ícones visíveis e corretos nos dois temas;
`test_self_audit` passando — nenhuma dependência nova entrou.

---

## Ordem e dependências

```
1. perf ─────────────── independente, ganho imediato, quase sem risco
2. chaves → EN ──┐      mecânica e grande; sozinha no commit
3. erro em core/ ─┼──→  4. i18n + tooltips
5. tema ────────────── independente das anteriores
6. ícones SVG ───────── depois de 2 e 4 (emoji-como-dado já removido)
```

As fatias 2 e 3 são pré-requisito da 4. A 5 pode ir a qualquer momento. A 6 vem por último
porque as fatias anteriores já removem os emojis que carregavam significado.

---

## Fora de escopo (decidido, não esquecido)

- **Cache de respostas do PyPI** — invalidação não vale o ganho (fatia 1).
- **Tempo mínimo de exibição do loader** — é o `sleep` com outro nome (fatia 1).
- **Página de glossário dedicada** — ajuda fora do momento da dúvida; tooltip chega melhor.
- **Babel/gettext e biblioteca de ícones** — dependências pesadas numa ferramenta que audita
  dependências (ADR-0009).
- **Traduzir `CONTEXT.md`, ADRs e enunciado** — documentação segue em português (convenção do
  workspace ES). Versões `.en.md`, incluindo `README.en.md`, ficam para **depois**.
- **Teste amarrando gloss da UI ao `CONTEXT.md`** — avaliado e dispensado; risco de divergência
  aceito conscientemente (fatia 4).
