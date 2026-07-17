# Ingestão do Projeto-Alvo por upload e por diretório

A US-01 pede selecionar o projeto "apontando para o diretório do código", mas a
implementação inicial só aceitava upload de ZIP/TAR. Decidimos suportar **os dois**: um
campo de caminho local (o Streamlit roda na máquina do dev, então o path resolve) somado
ao upload já existente.

Consequência: nenhum módulo pode falar `ZipInfo`/`TarInfo` diretamente. `filter.py` e
`import_parser.py` hoje acoplam-se a esses tipos e precisam passar a consumir uma fonte de
arquivos abstrata (listar caminhos, ler conteúdo), com implementação para archive e para
diretório. Foi esse acoplamento — e não a UI — o custo real da decisão.

Rejeitado: trocar tudo por diretório, o que jogaria fora `decompressor.py` e seus testes,
e impediria auditar um projeto que se recebe compactado.
