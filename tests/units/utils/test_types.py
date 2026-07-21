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

from utils.types import DeclarationEntry, Dependency, ExportRow, ReportRow

# O que um reader extrai de uma Declaração, antes de virar Dependência.
DECLARATION_FIELDS = {"package", "used_version", "origin"}

# A dependência auditada, como sai de `parsin` e é enriquecida por `analysis`.
DEPENDENCY_FIELDS = {
    "package",
    "used_version",
    "pypi_version",
    "status",
    "size",
    "age",
    "origin",
}

# A linha que alimenta a tabela do relatório, como sai de `normalize`. Carrega os
# mesmos campos da Dependência mais a nota de que Tamanho e Idade se referem à
# versão mais recente — o caso do Fantasma, que não tem Versão Usada. Aquilo era
# texto colado no valor ("1.2 MB (última versão)"); virou dado, para que a tela
# possa dizê-lo na língua dela (ADR-0010).
REPORT_FIELDS = DEPENDENCY_FIELDS | {"metrics_from_latest"}

# A ordem é o contrato: o cabeçalho do CSV sai daqui (ADR-0008), e trocar a ordem
# desalinha exports do mesmo Projeto-Alvo feitos em datas diferentes.
EXPORT_FIELDS_IN_ORDER = [
    "analysis_date",
    "project",
    "package",
    "category",
    "origin",
    "used_version",
    "pypi_version",
    "outdated",
    "size",
    "age",
]


def test_a_entrada_de_declaracao_declara_o_que_os_readers_extraem():
    """O reader lê o que a Declaração diz, e a Declaração não diz tudo.

    `Versão PyPI` e `Status` só existem depois de consultar o PyPI, então o
    registro do reader é menor que a Dependência — separá-los é o que impede
    anotar o reader com um formato que ele nunca preenche por inteiro.
    """
    assert set(DeclarationEntry.__annotations__) == DECLARATION_FIELDS


def test_a_entrada_de_declaracao_vira_dependencia_sem_perder_campo():
    """`normalize_dependency` acrescenta campos à entrada; nunca descarta nenhum."""
    assert DECLARATION_FIELDS <= DEPENDENCY_FIELDS


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
    carried_over = DEPENDENCY_FIELDS - {"status"}

    assert carried_over <= set(ExportRow.__annotations__)
