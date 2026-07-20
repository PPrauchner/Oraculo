# ORÁCULO

**O**rganizador e **R**astreador **A**utomático de **C**ódigo, **U**so de **L**ibraries e
**O**corrências.

Ferramenta de auditoria de dependências de projetos Python. Cruza o que um projeto
**declara** depender com o que seu código **realmente importa**, e confronta ambos com
o PyPI para avaliar a saúde das dependências.

## Language

### O que é analisado

**Projeto-Alvo**:
O projeto Python cujas dependências estão sendo auditadas. Nunca é o ORÁCULO em si.
_Avoid_: projeto, input, upload

**Declaração**:
Arquivo onde o Projeto-Alvo enuncia de quais pacotes ele depende (`pyproject.toml`,
`requirements.txt`, `requirements-dev.txt`, `environment.yml`). Define **quais** pacotes são
diretos, não em que versão. Um Projeto-Alvo pode ter várias, e todas valem.
_Avoid_: manifesto, config, arquivo de dependências

**Origem**:
De qual Declaração — e de qual seção dela — um pacote veio. É o que separa Dependência de
Produção de Dependência de Desenvolvimento.
_Avoid_: fonte, grupo, escopo

**Lock**:
O arquivo que registra a versão exata de cada pacote efetivamente resolvido (`uv.lock`,
`poetry.lock`). Define **em que versão**, não quais são diretos.
_Avoid_: lockfile, trava

**Exclusão**:
**Nome de pasta** que o usuário marcou para ficar fora da auditoria (ex.: `tests`, `docs`), e que
casa em qualquer profundidade: marcar `tests` exclui `tests/` e `src/tests/` (ADR-0007). Código em
Exclusão não gera imports nem declarações. Duas pastas de mesmo nome em níveis diferentes não se
distinguem — é o preço de nenhuma pasta oferecida na UI falhar em excluir.
_Avoid_: ignore, filtro, blacklist, caminho

### Identidade de um pacote

**Nome de Distribuição**:
O nome pelo qual um pacote é publicado no PyPI e escrito na Declaração (ex.: `PyYAML`,
`scikit-learn`).
_Avoid_: nome do pacote, nome real

**Nome de Import**:
O nome pelo qual o pacote é importado no código (ex.: `yaml`, `sklearn`). Não é
necessariamente igual ao Nome de Distribuição.
_Avoid_: módulo, nome do módulo

**Import Raiz**:
O primeiro segmento de um import, que é o que identifica o pacote (`django.core.cache` →
`django`). Imports relativos, módulos da stdlib e Módulos Próprios não são Imports Raiz.
_Avoid_: import, dependência usada

**Módulo Próprio**:
Pacote definido pelo próprio Projeto-Alvo (ex.: `core`, `utils`), reconhecível por existir
como pasta de topo com `__init__.py`. Não é dependência de ninguém e nunca é Fantasma.
_Avoid_: módulo local, interno, first-party

**Alias de Import**:
Caso em que o Nome de Import difere do Nome de Distribuição (`yaml` ↔ `PyYAML`).
Sem resolvê-lo, um mesmo pacote vira Fantasma e Zumbi ao mesmo tempo.
_Avoid_: mapeamento, tradução, de-para

### Categorias da auditoria

**Dependência Declarada**:
Pacote que aparece em alguma Declaração do Projeto-Alvo.
_Avoid_: dependência instalada, requisito

**Dependência de Produção**:
Dependência Declarada que o código principal precisa para rodar. Origem: `[project].dependencies`
ou `requirements.txt`.
_Avoid_: dependência real, runtime, main

**Dependência de Desenvolvimento**:
Dependência Declarada que serve ao trabalho sobre o código, não à execução dele. Origem:
`requirements-dev.txt`, `[dependency-groups]` ou `[project.optional-dependencies]`. Nunca é Zumbi:
muitas (ruff, mypy) não são importadas por ninguém, e as demais vivem justamente nas Exclusões.
_Avoid_: dev dependency, dependência opcional, extra

**Dependência Zumbi**:
Dependência de Produção cujo Nome de Distribuição não corresponde a nenhum Import Raiz
encontrado fora das Exclusões. Está paga, mas não usada.
_Avoid_: dependência morta, órfã, não utilizada

**Dependência Fantasma**:
Import Raiz que não corresponde a nenhuma Dependência Declarada. Funciona na máquina do
dev por vir de carona como transitiva, e quebra em outro ambiente.
_Avoid_: dependência implícita, oculta, faltante

**Dependência Desatualizada**:
Dependência cuja Versão Usada é anterior à versão mais recente publicada no PyPI.
_Avoid_: obsoleta, velha, defasada

**Categoria**:
Como uma dependência é classificada no relatório e na exportação: Zumbi, Fantasma ou
Saudável. É excludente — cada dependência sai em exatamente uma linha. Desatualizada
**não** é Categoria: é coluna própria, porque uma dependência pode ser Zumbi *e*
Desatualizada ao mesmo tempo.
_Avoid_: tipo, classe, status

**Saudável**:
Categoria da dependência que não é Zumbi nem Fantasma. Diz apenas que ela é declarada e
usada — **não** que esteja em dia: uma linha pode sair `Categoria=Saudável` com
`Desatualizada=Sim`. Não confundir com o Índice de Saúde, que é mais exigente e desconta
também as Desatualizadas.
_Avoid_: OK, saudável demais, em dia

### Métricas

**Versão Usada**:
A versão de um pacote que o Projeto-Alvo efetivamente executa. Vem do Lock quando existe;
uma Declaração não pinada (`>=3.0.1`) não determina Versão Usada por si só.
_Avoid_: versão atual, versão declarada, versão instalada

**Tamanho**:
Os bytes do artefato (wheel; sdist quando não há wheel) da Versão Usada, conforme
publicado no PyPI. Não é tamanho em disco nem inclui transitivas.
_Avoid_: peso, espaço, tamanho em disco

**Idade**:
Tempo entre a data de lançamento da Versão Usada no PyPI e hoje. Mede há quanto tempo o
Projeto-Alvo está parado naquela versão — não a idade do pacote.
_Avoid_: tempo de vida, antiguidade, defasagem

**Índice de Saúde**:
Proporção de Dependências Declaradas que não são Zumbis, Fantasmas nem Desatualizadas.
Mais exigente que a Categoria Saudável, que ignora Desatualizada.
_Avoid_: score, nota, percentual

### Ausência de valor

Duas ausências diferentes, que o relatório não pode confundir: uma é limite do que se sabe,
a outra é propriedade do que se auditou.

**Indeterminado**:
O ORÁCULO não tem como saber o valor. É o caso da Versão Usada sem Lock e sem pin — e, por
consequência, do Tamanho e da Idade que dependem dela. Um Lock resolveria.
_Avoid_: vazio, nulo, zero, desconhecido pelo PyPI

**Não Aplicável**:
O valor não existe para aquela dependência, por definição. É o caso da Origem de um Fantasma:
ele não vem de Declaração nenhuma, então não há seção de onde ter vindo. Nenhum arquivo a mais
preencheria isso.
_Avoid_: indisponível, faltando, sem dados

## Vocabulário do dado exportado

O CSV é contrato estável em inglês e não acompanha a língua da tela (ADR-0008). Estes são
os únicos valores que ele emite — traduzir para exibição é responsabilidade de
`utils/display.py`, e a tradução nunca alcança o arquivo:

| Coluna | Valores |
|---|---|
| `Category` | `Zombie` · `Ghost` · `Healthy` |
| `Origin` | `Production` · `Development` · `N/A` |
| `Status` | `Outdated` · `Up to date` · `Unknown` · `Invalid version` |
| `Outdated` | `Yes` · `No` |
| ausência | `Unknown` (Indeterminado) · `N/A` (Não Aplicável) |

O `Status` não é coluna do CSV: ele decide a coluna `Outdated` e aparece na tabela da tela.
Está aqui porque seus valores são identidade estável pela mesma razão que os das outras —
são comparados, não só exibidos.

Três vocabulários convivem, separados de propósito para que mexer num não alcance os
outros por acidente: a **chave interna** (`used_version`, snake_case), o **cabeçalho do
CSV** (`Used Version`, fixo em inglês, em `CSV_HEADER`) e o **rótulo da tela** (`Versão
Usada` / `Used Version`, em `locales/`). O glossário acima faz a ponte com o termo de
domínio em português.
