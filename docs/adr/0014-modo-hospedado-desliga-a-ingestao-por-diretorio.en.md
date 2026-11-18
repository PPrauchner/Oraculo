*[Versão em português](0014-modo-hospedado-desliga-a-ingestao-por-diretorio.md)*

# Hosted mode turns directory ingestion off

Narrows [ADR-0001](0001-ingestao-por-upload-e-por-diretorio.en.md). Directory ingestion
assumes Streamlit runs on the dev's machine, so a typed path resolves there. Published
on Streamlit Community Cloud, the same path resolves **on the server**: any visitor
could point at a folder of the container (the app's own repository, the installed
stdlib) and read it through the audit.

**Decided:** ADR-0001 holds for local execution. With the **hosted mode** on, the home
offers only upload — no radio, no path field — and opens no typed path even when the
session state asks for `ingestion_mode == "directory"`.

- The mode is turned on only by the `ORACULO_HOSTED` environment variable (`true` or
  `1`, case-insensitive). On Streamlit Cloud, a root key of the *Secrets* reaches the
  process that way; the code does not read `st.secrets` and does not depend on
  `.streamlit/secrets.toml` existing. Without the variable, nothing changes.
- The decision belongs to presentation: it lives in `utils/hosting.py` and in the home.
  `core/` does not know where it runs, and `open_directory`, `list_paths` and
  `read_text` do not change.
- The refusal targets the typed path, not the kind of source: upload and an in-memory
  Target Project follow the normal flow.

Rejected: detecting hosting by heuristic (hostname, mount path), which fails silently
when the platform changes; and hiding only the radio, which would let session state
reopen the door.
