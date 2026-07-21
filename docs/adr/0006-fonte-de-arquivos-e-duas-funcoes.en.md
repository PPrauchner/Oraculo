*[Versão em português](0006-fonte-de-arquivos-e-duas-funcoes.md)*

# The file source is two functions, not a type

ADR-0001 decided to ingest the Target Project by upload **and** by directory, and pointed to
the real cost: `filter.py` and `import_parser.py` speak `ZipInfo`/`TarInfo` directly. The
shape of the abstraction that replaces them was left open. This is that decision.

The contract is **two primitives**, in `core/ingestion/source.py`:

```
list_paths(source)        -> list[str]
read_text(source, path)   -> str | None
```

Nothing else. Taking stock of what the pipeline actually asks for shows that six callers
reduce to these two: `declaration_collector` and `lock_resolver` only iterate over (path,
content); `import_parser` wants the full list of paths (for `infer_own_modules`) and the
content of the `.py` files; `validate_archive_structure`, `get_unique_folders` and the
multiselect in `home.py` want only the paths. `iter_archive_texts` and the two functions in
`filter.py` come to derive from the primitives instead of reimplementing them.

**Reading by path, and not by member, is what kills the coupling.** As long as the read asks
for a `ZipInfo`/`TarInfo`, the type leaks to the caller, however much the surrounding
signature is changed. Switching the key to `str` resolves it, and preserves the laziness
`archive_walker` already defended: walking the index is cheap, decoding each file is not —
`read_text` is only called for what passed the filter.

**The abstraction exposes neither size nor date.** Size and Age come from PyPI (ADR-0004),
not from disk. That is what holds the contract to two functions instead of it becoming a
portable `stat`.

Shape: module functions with dispatch by `isinstance`, confined to `source.py` — the only
place in the project authorised to know `ZipFile`/`TarFile`. Rule 01 of the assignment
requires the procedural paradigm, which rules out the textbook answer (an abstract base class
with `ArchiveSource` and `DirectorySource`). `source` is the raw object: `ZipFile | TarFile |
Path`.

`dict[str, str]` enters as a fourth kind of source, mapping path to content. It costs two
lines in the dispatch and gives the test double for free: today `test_import_parser.py`,
`test_declaration_collector.py` and `test_lock_resolver.py` build real ZIPs via `BytesIO`
just to exercise logic that is about strings.

Rejected: **a NamedTuple of two closures** (`FileSource(list_paths=..., read_text=...)`),
which would dispense with the `isinstance` and give even cheaper doubles, but introduces a
type where Rule 01 asks that there be none. Also rejected the **eager snapshot**
(`load_project(source) -> dict[str, str]`), simpler than everything, yet it decodes the whole
project to use a fraction of it and loads it into memory.
