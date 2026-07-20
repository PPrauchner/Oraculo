"""
Formato dos registros que atravessam o pipeline de auditoria.

Responsabilidades:
- Descrever a Dependência auditada, como `parsin` a produz e `analysis` a enriquece.
- Descrever a linha exibida no relatório e a linha da exportação, que dela derivam.

A ADR-0011 introduz estes `TypedDict` como rede para a renomeação das chaves para
inglês (ADR-0008): num `dict` sem esquema, uma chave escrita errada não falha na
hora — o `.get()` devolve o default e o relatório sai vazio, sem erro e sem aviso.
Declarado o formato, o verificador cobra cada ponto de leitura.

Em tempo de execução isto continua sendo `dict` comum: sem instanciação, sem `self`,
sem método. Nenhuma regra de negócio mora aqui — quem classifica Zumbi é
`zombie_analizer`, quem calcula Idade é `pypi_client`. A Regra 01 (paradigma
procedural) proíbe modelar o domínio em objetos com estado e comportamento, e
`TypedDict` usa `class` como sintaxe de declaração de tipo, não como construtor:
é apagado em runtime e existe só para o verificador.

O glossário do `CONTEXT.md` faz a ponte entre o termo de domínio em português e o
identificador aqui — Pacote é `package`, Versão Usada é `used_version`. O rótulo
que o usuário lê no CSV é um terceiro vocabulário, e mora em `CSV_HEADER`.
"""

from typing import NotRequired, TypedDict

# Tamanho e Idade saem crus (bytes, dias) do PyPI, ou como o sentinela de
# indisponibilidade quando a Versão Usada não foi resolvida (ADR-0002/ADR-0004).
RawMetric = int | str


class DeclarationEntry(TypedDict):
    """O que um reader extrai de uma Declaração, antes de virar Dependência.

    Menor que a Dependência de propósito: a Declaração diz o Pacote e, quando
    fixa versão, a Versão Usada. `pypi_version` e `status` só existem depois de
    consultar o PyPI, e declará-los aqui seria prometer campo que o reader nunca
    preenche.
    """

    package: str
    # Vazia quando a Declaração não fixa versão — pin exato é o único que define
    # Versão Usada (ADR-0002), e o Lock resolve o resto depois.
    used_version: str
    # Preenchida pelos readers que distinguem grupo de desenvolvimento; é ela que
    # isenta a Dependência de Desenvolvimento de virar Zumbi (ADR-0003).
    origin: NotRequired[str]


class Dependency(TypedDict):
    """A Dependência auditada, como circula de `parsin` até o relatório."""

    package: str
    used_version: str
    pypi_version: str
    status: str
    # Preenchidos por `analysis` a partir do PyPI, ausentes até lá.
    size: NotRequired[RawMetric]
    age: NotRequired[RawMetric]
    # Fantasma não tem Declaração, logo não tem Origem (CONTEXT.md).
    origin: NotRequired[str]


class ReportRow(TypedDict):
    """A linha exibida na tabela do relatório, como sai de `normalize`."""

    package: str
    used_version: str
    pypi_version: str
    status: str
    # Já formatados para leitura ("1.2 MB", "30 dias"), diferente da exportação.
    size: str
    age: str
    origin: str


class CategorySummary(TypedDict):
    """As agregações de uma Categoria, como `summarize_category` as produz.

    Ficou de fora da renomeação da ADR-0008 por não tocar o CSV nem descrever uma
    dependência — mas é registro que atravessa `core/report/` até a tela, e o mesmo
    argumento do ADR-0011 vale: chave escrita errada num `dict` solto devolve o
    default e a métrica sai vazia, sem erro e sem aviso.

    `None` em `total_size`/`average_age` não é zero: significa que nenhuma
    dependência da categoria teve a métrica medida, e somar ou mediar o
    Indeterminado como 0 inventaria um número que o PyPI não deu (ADR-0004).
    """

    count: int
    total_size: float | None
    average_age: float | None
    # Quantas ficaram de fora de cada agregação, para que a média não engane quem lê.
    missing_size: int
    missing_age: int


class ExportRow(TypedDict):
    """A linha do CSV, como sai de `build_export_rows`.

    A ordem de declaração é a ordem das colunas do arquivo (ADR-0008), e os
    rótulos que o usuário lê saem de `CSV_HEADER` — nunca destas chaves.
    """

    analysis_date: str
    project: str
    package: str
    category: str
    origin: str
    used_version: str
    pypi_version: str
    # Desatualizada é coluna própria, e não valor de Categoria: uma dependência
    # pode ser Zumbi *e* Desatualizada, e um campo só perderia uma das leituras.
    outdated: str
    # Crus, nunca formatados: o CSV é para diffing e concatenação ao longo do
    # tempo, não para leitura humana direta — essa é a `normalize`.
    size: RawMetric
    age: RawMetric
