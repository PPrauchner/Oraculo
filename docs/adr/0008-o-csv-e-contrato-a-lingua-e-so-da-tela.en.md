*[Versão em português](0008-o-csv-e-contrato-a-lingua-e-so-da-tela.md)*

# The CSV is a contract; the language is the screen's alone

ORÁCULO is going to gain a language selector (pt-BR / en). At the same time, the keys of the
dependency dictionaries — `Pacote`, `Versão Usada`, `Status` — are in Portuguese, against the
English-code convention. The two changes collide in the same place: `export_to_csv` builds the
header from `report_data[0].keys()`, so the CSV header **is** the internal key. Renaming the
keys rewrites the exported file; letting the selector reach it rewrites the file on every
click.

**The internal keys and the CSV header are English, fixed. The language selector does not
reach them.** Switching the language changes label, text and explanation on screen; the
downloaded file comes out identical in both languages. This preserves the property US-07
depends on: **any two exports of the same Target Project are comparable**, whichever language
they were generated in. The header stops being a side effect of the dictionary and becomes an
explicit decision.

The accepted cost is that the CSV stops speaking the assignment's language: whoever opens the
file reads `Package,Used Version,Category` while `CONTEXT.md` and the ADRs speak Pacote,
Versão Usada and Categoria. The bridge between the two vocabularies becomes the glossary's
responsibility, which is why it records the English identifier of each domain term.

Rejected: **the header following the UI**. It is what the user would expect on seeing the
screen in Portuguese, and precisely for that reason it is the trap — auditing the same project
in March with the UI in Portuguese and in June with the UI in English produces two files that
do not line up, and the time series breaks silently, with no error and no warning. A selector
of appearance cannot have the power to corrupt historical data.

Also rejected: **a header fixed in Portuguese**, with an explicit mapping from internal key to
PT label. It resolves stability as well as the adopted option and even keeps old exports
valid, but it pays a permanent translation layer in `core/report/` to serve one of the two
languages — and picks, as the eternal default of the data format, the language the product has
just stopped assuming.
