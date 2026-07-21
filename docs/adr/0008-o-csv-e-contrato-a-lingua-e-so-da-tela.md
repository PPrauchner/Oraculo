*[English version](0008-o-csv-e-contrato-a-lingua-e-so-da-tela.en.md)*

# O CSV é contrato; a língua é só da tela

O ORÁCULO vai ganhar um seletor de língua (pt-BR / en). Ao mesmo tempo, as chaves dos
dicionários de dependência — `Pacote`, `Versão Usada`, `Status` — estão em português, contra a
convenção de código em inglês. As duas mudanças colidem no mesmo lugar: `export_to_csv` monta
o cabeçalho a partir de `report_data[0].keys()`, então o cabeçalho do CSV **é** a chave interna.
Renomear as chaves reescreve o arquivo exportado; deixar o seletor alcançá-lo reescreve o
arquivo a cada clique.

**As chaves internas e o cabeçalho do CSV são inglês, fixo. O seletor de língua não os
alcança.** Trocar a língua muda rótulo, texto e explicação na tela; o arquivo baixado sai
idêntico nas duas línguas. Isso preserva a propriedade de que a US-07 depende: **quaisquer dois
exports do mesmo Projeto-Alvo são comparáveis**, tenham sido gerados em que língua for. O
cabeçalho deixa de ser um efeito colateral do dicionário e passa a ser uma decisão explícita.

O custo aceito é que o CSV deixa de falar a língua do enunciado: quem abre o arquivo lê
`Package,Used Version,Category` enquanto o `CONTEXT.md` e os ADRs falam Pacote, Versão Usada e
Categoria. A ponte entre os dois vocabulários passa a ser responsabilidade do glossário, que
por isso registra o identificador em inglês de cada termo do domínio.

Rejeitado: **cabeçalho seguindo a UI**. É o que o usuário esperaria ao ver a tela em português,
e exatamente por isso é a armadilha — auditar o mesmo projeto em março com a UI em português e
em junho com a UI em inglês produz dois arquivos que não se alinham, e a série temporal quebra
em silêncio, sem erro e sem aviso. Um seletor de aparência não pode ter poder de corromper
dados históricos.

Rejeitado também: **cabeçalho fixo em português**, com mapeamento explícito de chave interna
para rótulo PT. Resolve a estabilidade tão bem quanto a opção adotada e ainda mantém exports
antigos válidos, mas paga uma camada de tradução permanente em `core/report/` para servir a uma
das duas línguas — e escolhe, como padrão eterno do formato de dados, a língua que o produto
acabou de deixar de assumir.
