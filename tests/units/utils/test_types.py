"""
Guarda o formato dos registros que atravessam o pipeline.

A ADR-0011 introduz esses `TypedDict` como rede para a renomeação das chaves para
inglês (ADR-0008): chave errada num `dict` solto não falha na hora — o `.get()`
devolve o default e o relatório sai vazio sem reclamar. Declarado o formato, o
verificador cobra cada ponto de leitura.

A rede só vale enquanto descrever a realidade. Estes testes casam o formato
declarado contra o que o pipeline de fato produz, para que os dois não se separem
em silêncio durante a migração.

Responsabilidades:
- Guardar quais campos cada registro tem.
- Guardar a ordem dos campos da exportação, que é a ordem das colunas do CSV.
"""

from utils.types import Dependency, ExportRow, ReportRow

# A dependência auditada, como sai de `parsin` e é enriquecida por `analysis`.
DEPENDENCY_FIELDS = {
    "Pacote",
    "Versão Usada",
    "Versão PyPI",
    "Status",
    "Tamanho",
    "Idade",
    "Origem",
}

# A linha exibida na tabela do relatório, como sai de `normalize`.
REPORT_FIELDS = DEPENDENCY_FIELDS

# A ordem é o contrato: o cabeçalho do CSV sai daqui (ADR-0008), e trocar a ordem
# desalinha exports do mesmo Projeto-Alvo feitos em datas diferentes.
EXPORT_FIELDS_IN_ORDER = [
    "Data da Análise",
    "Projeto",
    "Pacote",
    "Categoria",
    "Origem",
    "Versão Usada",
    "Versão PyPI",
    "Desatualizada",
    "Tamanho",
    "Idade",
]


def test_a_dependencia_declara_os_campos_que_o_pipeline_produz():
    """O formato declarado é o que `parsin` e `analysis` de fato preenchem."""
    assert set(Dependency.__annotations__) == DEPENDENCY_FIELDS


def test_a_linha_do_relatorio_declara_os_campos_que_normalize_produz():
    """`normalize` monta a linha exibida; o formato declarado acompanha."""
    assert set(ReportRow.__annotations__) == REPORT_FIELDS


def test_a_linha_da_exportacao_declara_os_campos_na_ordem_do_csv():
    """A ordem dos campos é a ordem das colunas do arquivo baixado.

    Guardar a ordem, e não só o conjunto, é o que impede que uma reordenação
    silenciosa quebre a comparabilidade entre exports que a US-07 depende.
    """
    assert list(ExportRow.__annotations__) == EXPORT_FIELDS_IN_ORDER


def test_nenhum_campo_da_dependencia_some_da_exportacao():
    """A exportação acrescenta eixos (Data, Projeto, Categoria), nunca perde dados.

    `Status` é a exceção deliberada: na exportação ele vira a coluna `Desatualizada`,
    porque uma dependência pode ser Zumbi *e* Desatualizada, e um campo só perderia
    uma das duas leituras.
    """
    carried_over = DEPENDENCY_FIELDS - {"Status"}

    assert carried_over <= set(ExportRow.__annotations__)
