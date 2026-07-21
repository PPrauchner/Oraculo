*[English version](0007-exclusao-casa-por-nome-de-pasta.en.md)*

# A Exclusão casa por nome de pasta, em qualquer profundidade

O multiselect oferecia pastas que o filtro era incapaz de excluir. `get_unique_folders`
coletava todos os segmentos do caminho, em qualquer profundidade; `is_path_in_ignored_folders`
casava só a partir da raiz. Tudo que não estivesse no primeiro nível era oferecido na UI e
ignorado pelo filtro: o usuário marcava `tests`, nada reclamava, e os arquivos continuavam
sendo auditados (issue #26).

Uma **Exclusão é o nome de uma pasta, e vale em qualquer profundidade**. Marcar `tests`
exclui `tests/` e `src/tests/`. As duas funções passam a falar da mesma coisa, que é o que
garante a propriedade que faltava: nenhuma pasta oferecida deixa de excluir. Um arquivo cujo
nome coincide com a Exclusão não é excluído — Exclusão é pasta, não caminho.

O custo aceito é que duas pastas de mesmo nome em níveis diferentes deixam de se distinguir:
quem marca `tests` não consegue excluir `src/tests` mantendo `tests/`. Em troca, a UI para
de mentir, e quem baixa o Projeto-Alvo do GitHub consegue excluir `tests` — o que a semântica
ancorada na raiz não permitia, porque o "Download ZIP" embrulha tudo em `<repo>-<branch>/`.

Ortogonal e também adotado: a pasta-embrulho **some na normalização** da fonte de arquivos
(ADR-0006), antes de qualquer filtragem. Isso não era opcional — sem descascá-la, o mesmo
projeto auditado como diretório e como ZIP daria relatórios diferentes, e o ADR-0001 exige
que deem o mesmo.

Rejeitado: **oferecer só o que o filtro sabe casar**, mantendo a semântica ancorada na raiz.
Ou a UI ofereceria apenas o primeiro nível — e um projeto em layout `src/` não conseguiria
excluir `src/tests` sem excluir `src` inteiro, perdendo todo o código —, ou ofereceria
caminhos relativos completos, trocando nomes curtos por uma lista longa e ainda assim sem
resolver o embrulho sozinha.
