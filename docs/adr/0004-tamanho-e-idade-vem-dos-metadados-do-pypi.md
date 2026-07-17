# Tamanho e Idade vêm dos metadados do PyPI

O enunciado exige Tamanho e Idade sem definir de quê. Definimos Tamanho como os bytes do
wheel (sdist como fallback) da Versão Usada, e Idade como hoje menos o `upload_time` dessa
mesma versão — ambos lidos de `releases[versão]` na resposta de `/pypi/NAME/json`, a mesma
requisição que já traz a versão mais recente. Um request por pacote resolve os três dados.

Escolhemos metadados em vez de medir `site-packages` porque a ingestão é dupla (ADR-0001):
tamanho em disco seria impossível no modo upload — venv não vai no ZIP — e impossível para
Fantasmas, que sequer estão instalados. Um mesmo pacote precisa dar o mesmo número nos dois
modos, senão a métrica não significa nada.

Consequência a não "corrigir": Tamanho não é o espaço ocupado em disco (o wheel é
comprimido) e não inclui transitivas. Como a US-07 compara relatórios ao longo do tempo,
mudar essa definição depois invalida todo o histórico já exportado.
