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
`TypedDict` usa `class` como sintaxe de declaração de tipo, não como construtor.

As chaves ainda estão em português porque a migração da ADR-0008 é o passo seguinte:
o formato precisa existir *antes* dela, senão não há o que verificar. A sintaxe é a
funcional porque "used_version" não é identificador Python.
"""

from typing import NotRequired, TypedDict

# Tamanho e Idade saem crus (bytes, dias) do PyPI, ou como o sentinela de
# indisponibilidade quando a Versão Usada não foi resolvida (ADR-0002/ADR-0004).
RawMetric = int | str

DeclarationEntry = TypedDict(
    "DeclarationEntry",
    {
        "package": str,
        # Vazia quando a Declaração não fixa versão — pin exato é o único que
        # define Versão Usada (ADR-0002), e o Lock resolve o resto depois.
        "used_version": str,
        # Preenchida pelos readers que distinguem grupo de desenvolvimento; é ela
        # que isenta a Dependência de Desenvolvimento de virar Zumbi (ADR-0003).
        "origin": NotRequired[str],
    },
)

Dependency = TypedDict(
    "Dependency",
    {
        "package": str,
        "used_version": str,
        "pypi_version": str,
        "status": str,
        # Preenchidos por `analysis` a partir do PyPI, ausentes até lá.
        "Tamanho": NotRequired[RawMetric],
        "Idade": NotRequired[RawMetric],
        # Fantasma não tem Declaração, logo não tem Origem (CONTEXT.md).
        "origin": NotRequired[str],
    },
)

ReportRow = TypedDict(
    "ReportRow",
    {
        "package": str,
        "used_version": str,
        "pypi_version": str,
        "status": str,
        # Já formatados para leitura ("1.2 MB", "30 dias"), diferente da exportação.
        "Tamanho": str,
        "Idade": str,
        "origin": str,
    },
)

ExportRow = TypedDict(
    "ExportRow",
    {
        # A ordem de declaração é a ordem das colunas do CSV (ADR-0008).
        "Data da Análise": str,
        "Projeto": str,
        "package": str,
        "Categoria": str,
        "origin": str,
        "used_version": str,
        "pypi_version": str,
        # Desatualizada é coluna própria, e não valor de Categoria: uma dependência
        # pode ser Zumbi *e* Desatualizada, e um campo só perderia uma das leituras.
        "Desatualizada": str,
        # Crus, nunca formatados: o CSV é para diffing e concatenação ao longo do
        # tempo, não para leitura humana direta — essa é a `normalize`.
        "Tamanho": RawMetric,
        "Idade": RawMetric,
    },
)
