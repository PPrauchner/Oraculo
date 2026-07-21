*[Versão em português](0001-ingestao-por-upload-e-por-diretorio.md)*

# Target Project ingestion by upload and by directory

US-01 asks to select the project "by pointing to the code directory", but the initial
implementation only accepted ZIP/TAR upload. We decided to support **both**: a local-path
field (Streamlit runs on the dev's machine, so the path resolves) on top of the existing
upload.

Consequence: no module may speak `ZipInfo`/`TarInfo` directly. `filter.py` and
`import_parser.py` today couple to those types and must move to consuming an abstract file
source (list paths, read content), with an implementation for archive and for directory. It
was this coupling — not the UI — that was the real cost of the decision.

Rejected: swapping everything for directory, which would throw away `decompressor.py` and
its tests, and would prevent auditing a project received compressed.
