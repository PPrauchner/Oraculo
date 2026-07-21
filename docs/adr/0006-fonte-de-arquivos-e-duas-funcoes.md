*[English version](0006-fonte-de-arquivos-e-duas-funcoes.en.md)*

# A fonte de arquivos são duas funções, não um tipo

O ADR-0001 decidiu ingerir o Projeto-Alvo por upload **e** por diretório, e apontou o custo
real: `filter.py` e `import_parser.py` falam `ZipInfo`/`TarInfo` direto. Ficou em aberto a
forma da abstração que os substitui. Esta é a decisão.

O contrato é de **duas primitivas**, em `core/ingestion/source.py`:

```
list_paths(source)        -> list[str]
read_text(source, path)   -> str | None
```

Nada mais. Levantar o que o pipeline de fato pede mostra que seis chamadores se reduzem a
essas duas: `declaration_collector` e `lock_resolver` só iteram (caminho, conteúdo);
`import_parser` quer a lista completa de caminhos (para `infer_own_modules`) e o conteúdo
dos `.py`; `validate_archive_structure`, `get_unique_folders` e o multiselect da `home.py`
querem só os caminhos. `iter_archive_texts` e as duas funções do `filter.py` passam a
derivar das primitivas em vez de reimplementá-las.

**Ler por caminho, e não por membro, é o que mata o acoplamento.** Enquanto a leitura pedir
um `ZipInfo`/`TarInfo`, o tipo vaza para quem chama, por mais que se troque a assinatura ao
redor. Trocar a chave para `str` resolve, e preserva a preguiça que o `archive_walker` já
defendia: percorrer o índice é barato, decodificar cada arquivo não — `read_text` só é
chamada para o que passou pelo filtro.

**A abstração não expõe tamanho nem data.** Tamanho e Idade vêm do PyPI (ADR-0004), não do
disco. É o que segura o contrato em duas funções em vez de virar um `stat` portátil.

Forma: funções de módulo com despacho por `isinstance`, confinado a `source.py` — o único
lugar do projeto autorizado a conhecer `ZipFile`/`TarFile`. A Regra 01 do enunciado exige
paradigma procedural, o que descarta a resposta de manual (uma classe base abstrata com
`ArchiveSource` e `DirectorySource`). `source` é o objeto cru: `ZipFile | TarFile | Path`.

`dict[str, str]` entra como quarta espécie de fonte, mapeando caminho para conteúdo. Custa
duas linhas no despacho e dá o dublê de teste de graça: hoje `test_import_parser.py`,
`test_declaration_collector.py` e `test_lock_resolver.py` constroem ZIPs de verdade via
`BytesIO` só para exercitar lógica que é de string.

Rejeitado: **NamedTuple de dois closures** (`FileSource(list_paths=..., read_text=...)`),
que dispensaria o `isinstance` e daria dublês ainda mais baratos, mas introduz um tipo onde
a Regra 01 pede que não haja nenhum. Rejeitado também o **snapshot ansioso**
(`load_project(source) -> dict[str, str]`), mais simples que tudo, porém decodifica o
projeto inteiro para usar uma fração dele e o carrega na memória.
