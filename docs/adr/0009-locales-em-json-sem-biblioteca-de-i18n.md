*[English version](0009-locales-em-json-sem-biblioteca-de-i18n.en.md)*

# Locales em JSON, sem biblioteca de i18n

O ORÁCULO passa a oferecer a interface em português e inglês. O caminho canônico para isso é
`gettext`/Babel: extração automática, arquivos `.po`, pluralização e contexto — resolvido há
décadas e conhecido por qualquer revisor.

**A tradução vive em `locales/en.json` e `locales/pt.json`, resolvida por uma função própria,
sem nenhuma dependência nova.** São cerca de 60 rótulos, sem pluralização e sem interpolação
complexa; o que Babel resolve a mais que isso é problema que este produto não tem.

O motivo decisivo é outro, e é específico deste projeto: **o ORÁCULO é uma ferramenta que
denuncia dependências que o projeto carrega sem precisar, e ele se audita a si mesmo em
`tests/integration/test_self_audit.py`.** Adicionar Babel — megabytes e uma etapa de compilação
`.po` → `.mo` — para traduzir 60 strings colocaria na própria Declaração exatamente o tipo de
peso que o produto existe para apontar. A ferramenta precisa aguentar o próprio critério.

O formato é JSON, e não um `dict` em módulo Python, por coerência com os registries
`EXTRATORES`/`READERS`: lá, suportar um novo formato de arquivo é escrever uma função e
decorá-la, sem `if` novo em `pages/`. Aqui, suportar uma nova língua é acrescentar um arquivo,
sem tocar em código. A mesma ideia, aplicada duas vezes.

O que o JSON perde em relação ao módulo Python é a dificuldade de publicar meia tradução — um
`dict` ao menos fica visivelmente assimétrico ao lado do outro. Isso é recomprado por duas
garantias: **chave ausente cai para o inglês** (a tela fica bilingue por um instante, nunca
quebrada nem cheia de identificador cru), e **um teste exige que os dois arquivos tenham
exatamente o mesmo conjunto de chaves**, que é o que transforma "esqueci de traduzir" em falha
de build em vez de descoberta em produção.

O padrão é inglês, porque o projeto agora serve de portfólio e o público default deixou de ser
a banca. A escolha persiste em `?lang=`, então um link em português continua compartilhável. A
documentação segue em português (convenção do workspace); versões `.en.md` ficam para depois.

Ortogonal e já decidido: o seletor **não alcança o CSV**, que é contrato fixo em inglês
(ADR-0008). Trocar a língua muda a tela e nada no arquivo exportado.
