"""
Testes da tradução do dado do relatório para o texto que a tabela mostra.

`core/report/` devolve identidade e dado — o Status como identidade estável, o
Tamanho em bytes, a Idade em dias (ADR-0010). Quem escolhe a unidade, a redação e
a língua é esta camada, do mesmo jeito que `utils/messages.py` faz com os códigos
de erro de `core/ingestion/`.

Antes disso `normalize` devolvia "30 dias" e "(última versão)" prontos: com
`?lang=en` a tabela respondia em português e não havia mais o que traduzir, porque
o dado já tinha virado frase.

Responsabilidades:
- Guardar que Tamanho, Idade e Status saem na língua da tela.
- Guardar que a coluna da tabela é rótulo traduzido, não chave interna.
- Guardar que as duas ausências continuam distintas ao serem exibidas.
"""

import pytest

import utils.i18n
from utils.constants import (
    ORIGIN_DEVELOPMENT,
    ORIGIN_PRODUCTION,
    ORIGIN_UNAVAILABLE,
    STATUS_INVALID_VERSION,
    STATUS_OUTDATED,
    STATUS_UNKNOWN,
    STATUS_UP_TO_DATE,
    UNKNOWN,
)
from utils.display import (
    REPORT_COLUMNS,
    display_rows,
    format_age,
    format_size,
    origin_label,
    status_label,
)
from utils.i18n import available_languages, load_locale, translate
from utils.types import ReportRow


@pytest.fixture
def screen_language(monkeypatch: pytest.MonkeyPatch):
    """Finge a língua da requisição atual, que é o que `?lang=` decide."""

    def use(language: str) -> None:
        monkeypatch.setattr(utils.i18n.st, "query_params", {"lang": language})

    return use


def _row(**overrides) -> ReportRow:
    """Uma linha do relatório como `normalize` a devolve: dado cru, sem frase."""
    row: ReportRow = {
        "package": "pandas",
        "used_version": "1.5.0",
        "pypi_version": "2.0.0",
        "status": STATUS_OUTDATED,
        "size": 2 * 1024 * 1024,
        "age": 30,
        "origin": ORIGIN_PRODUCTION,
        "metrics_from_latest": False,
    }
    row.update(overrides)  # type: ignore[typeddict-item]
    return row


# ============ Tamanho e Idade ============


def test_o_tamanho_sai_na_unidade_legivel():
    """MB e KB são símbolo de unidade, não palavra: não mudam com a língua."""
    assert format_size(2 * 1024 * 1024) == "2.0 MB"
    assert format_size(500 * 1024) == "500.0 KB"


@pytest.mark.parametrize("language", available_languages())
def test_a_idade_conta_os_dias_na_lingua_da_tela(screen_language, language: str):
    """"30 dias" era frase pronta dentro de `core/`; agora nasce do locale."""
    screen_language(language)

    assert format_age(30) == translate("report.age.days", language).format(days=30)


@pytest.mark.parametrize("language", available_languages())
def test_um_dia_so_nao_sai_no_plural(screen_language, language: str):
    """Plural é decisão de língua, e por isso mora no locale, não no formatador."""
    screen_language(language)

    assert format_age(1) == translate("report.age.day", language).format(days=1)
    assert format_age(1) != format_age(2)


@pytest.mark.parametrize("language", available_languages())
def test_a_metrica_nao_medida_sai_como_indeterminado(screen_language, language: str):
    """Sem Versão Usada resolvida não há número a exibir — e nunca 0 (ADR-0004)."""
    screen_language(language)
    expected = translate("report.value.unknown", language)

    assert format_size(UNKNOWN) == expected
    assert format_age(UNKNOWN) == expected


# ============ Status e Origem ============


@pytest.mark.parametrize("language", available_languages())
@pytest.mark.parametrize(
    "status", [STATUS_OUTDATED, STATUS_UP_TO_DATE, STATUS_INVALID_VERSION, STATUS_UNKNOWN]
)
def test_todo_status_do_vocabulario_tem_rotulo_na_lingua_da_tela(
    screen_language, language: str, status: str
):
    """Status sem rótulo chegaria ao usuário como identificador cru.

    A identidade continua em inglês porque é comparada (`build_export_rows`); o que
    muda com a língua é só o texto.
    """
    screen_language(language)
    labels = set(load_locale(language).values())

    assert status_label(status) in labels


@pytest.mark.parametrize("language", available_languages())
def test_a_origem_distingue_producao_de_desenvolvimento_na_tela(
    screen_language, language: str
):
    """A Origem é o que separa Produção de Desenvolvimento (ADR-0003)."""
    screen_language(language)

    assert origin_label(ORIGIN_PRODUCTION) == translate("report.origin.production", language)
    assert origin_label(ORIGIN_DEVELOPMENT) == translate(
        "report.origin.development", language
    )


@pytest.mark.parametrize("language", available_languages())
def test_as_duas_ausencias_continuam_distintas_na_tela(screen_language, language: str):
    """Indeterminado e Não Aplicável não colapsam num rótulo só (CONTEXT.md).

    A Origem de um Fantasma não existe por definição; o Tamanho sem Versão Usada
    existe e não foi medido. Só a segunda diz ao usuário que adotar um Lock
    melhoraria o relatório dele.
    """
    screen_language(language)

    assert origin_label(ORIGIN_UNAVAILABLE) != format_size(UNKNOWN)


# ============ A tabela ============


@pytest.mark.parametrize("language", available_languages())
def test_a_coluna_da_tabela_e_rotulo_traduzido_nao_chave_interna(
    screen_language, language: str
):
    """A chave interna é contrato do CSV (ADR-0008) e não pode chegar à tela."""
    screen_language(language)

    columns = list(display_rows([_row()])[0])

    assert columns == [translate(key, language) for key in REPORT_COLUMNS.values()]
    assert set(columns).isdisjoint(REPORT_COLUMNS)


@pytest.mark.parametrize("language", available_languages())
def test_a_linha_da_tabela_traduz_status_idade_e_origem(screen_language, language: str):
    """A célula é texto de tela: nenhuma identidade estável sobrevive à renderização."""
    screen_language(language)

    cell = display_rows([_row()])[0]
    by_column = dict(zip(REPORT_COLUMNS, cell.values()))

    assert by_column["status"] == translate("report.status.outdated", language)
    assert by_column["age"] == translate("report.age.days", language).format(days=30)
    assert by_column["origin"] == translate("report.origin.production", language)
    assert by_column["package"] == "pandas"  # dado do pacote, não rótulo


@pytest.mark.parametrize("language", available_languages())
def test_o_fantasma_explicita_que_a_metrica_e_da_versao_mais_recente(
    screen_language, language: str
):
    """Fantasma não tem Versão Usada: Tamanho/Idade referem a mais recente (ADR-0004).

    Sem a nota, a tabela alegaria sobre a versão que o Projeto-Alvo roda um número
    que descreve outra.
    """
    screen_language(language)
    note = translate("report.metric.latest_version", language)

    cells = list(display_rows([_row(metrics_from_latest=True)])[0].values())
    by_column = dict(zip(REPORT_COLUMNS, cells))

    assert note in by_column["size"]
    assert note in by_column["age"]


@pytest.mark.parametrize("language", available_languages())
def test_a_nota_da_versao_mais_recente_nao_anota_o_que_nao_foi_medido(
    screen_language, language: str
):
    """Sem número, não há de que versão o número seria — a nota não se aplica."""
    screen_language(language)
    note = translate("report.metric.latest_version", language)

    cells = list(
        display_rows([_row(metrics_from_latest=True, size=UNKNOWN, age=UNKNOWN)])[0].values()
    )

    assert all(note not in cell for cell in cells)
