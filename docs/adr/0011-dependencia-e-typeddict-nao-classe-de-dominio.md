*[English version](0011-dependencia-e-typeddict-nao-classe-de-dominio.en.md)*

# A dependência é um `TypedDict`, não uma classe de domínio

A Regra 01 do enunciado exige **paradigma procedural: sem classes de domínio**. Este ADR
introduz `class Dependency(TypedDict)` e por isso precisa existir — quem ler o código sem
contexto vai ler isso como violação da regra.

O gatilho é a tradução das chaves para inglês (ADR-0008): `Pacote` → `package`, `Versão Usada`
→ `used_version`, e assim por diante, em 383 ocorrências espalhadas por 25 arquivos. Uma
renomeação mecânica dessa escala, num dicionário sem esquema, é exatamente o tipo de mudança em
que uma chave escapa — e uma chave errada num `dict` solto não falha na hora: ela devolve
`KeyError` no meio da UI, ou pior, um `.get()` devolve `None` e o relatório mostra vazio sem
reclamar.

**A dependência passa a ser descrita por um `TypedDict`.** Em tempo de execução ela continua
sendo um `dict` comum: sem instanciação, sem `self`, sem método, sem comportamento. Nenhuma
regra de negócio se muda para dentro dela — quem classifica Zumbi continua sendo
`zombie_analizer`, quem calcula Idade continua sendo `pypi_client`. As funções seguem recebendo
e devolvendo dicionários, e o pipeline continua uma sequência de transformações.

O que a Regra 01 proíbe é modelar o domínio em objetos que carregam estado e comportamento —
um `Dependency` com `.is_zombie()` e `.age_in_days` seria a violação real, e não é isso que
está sendo feito. `TypedDict` usa a palavra `class` como sintaxe de declaração de tipo, não
como construtor de objeto; ele é apagado em runtime e existe só para o verificador de tipos.
A convenção do projeto já exige type hints em todo parâmetro e retorno — isto é a mesma
exigência aplicada ao formato do dicionário, e não uma mudança de paradigma.

O ganho é conhecido e imediato: durante a renomeação, uma chave escrita errada vira erro de
verificação, não surpresa em runtime. Os 200 testes cobrem muito, mas não cobrem todo caminho
de leitura de chave na UI, que é precisamente onde o `dict` solto falha calado.

Rejeitado: **constantes para os nomes de chave** (`dep[KEY_PACKAGE]`). Pega o typo na hora, sem
sintaxe de classe nenhuma, e por isso foi a alternativa mais séria. Mas polui os 383 pontos de
leitura com indireção, não diz nada sobre o *tipo* do valor, e não descreve o registro como um
todo — não há um lugar onde esteja escrito quais campos uma dependência tem.

Rejeitado: **manter `dict` solto**. É a leitura mais conservadora da Regra 01 e não custa nada
hoje, mas escolhe correr o risco justamente na mudança que o cria.
