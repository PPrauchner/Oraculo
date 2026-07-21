"""
A escolha de língua exercitada pela tela, e não só pela função que traduz.

O que o ADR-0009 promete só existe de verdade no runtime do Streamlit: abrir em
inglês, trocar pelo seletor, sobreviver ao refresh em `?lang=`. `AppTest` roda a
página de verdade — e vem dentro do próprio Streamlit, então provar isto não custa
nenhuma dependência nova.

Responsabilidades:
- Guardar o padrão inglês e o efeito do seletor sobre a URL.
- Guardar que nenhum rótulo traduzido encosta em `session_state`.
- Guardar que a tela fala uma língua só, títulos de navegação inclusive.
- Guardar que trocar de língua não derruba o Projeto-Alvo já carregado.

O título da home é lido em `app.header`, e não em `app.title`: a issue #50 baixou-o um
nível para que as seções coubessem na hierarquia. O que se afere aqui continua sendo a
língua do título, não o tamanho dele.
"""

import ast
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from utils.i18n import available_languages, load_locale, translate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_PAGE = str(PROJECT_ROOT / "pages" / "home.py")
ENTRY_POINT = str(PROJECT_ROOT / "main.py")


def _run(lang: str | None = None) -> AppTest:
    """Abre a página inicial como um navegador abriria, com ou sem `?lang=`.

    Args:
        lang: Valor de `?lang=` na URL. `None` para uma URL sem o parâmetro.

    Returns:
        A aplicação já executada.
    """
    app = AppTest.from_file(HOME_PAGE, default_timeout=30)

    if lang is not None:
        app.query_params["lang"] = lang

    return app.run()


def test_the_app_opens_in_english_without_a_lang_in_the_url():
    """Padrão inglês: o projeto virou portfólio e a banca deixou de ser o público."""
    app = _run()

    assert app.header[0].value == translate("home.title", "en")


def test_a_shared_link_arrives_already_translated():
    """`?lang=pt` na URL é o que faz o link ser compartilhável e sobreviver ao refresh."""
    app = _run("pt")

    assert app.header[0].value == translate("home.title", "pt")
    assert app.sidebar.markdown[1].value == translate("sidebar.subtitle", "pt")


@pytest.mark.parametrize("language", available_languages())
def test_the_sidebar_no_longer_teaches_ignoring_virtual_environments(language: str):
    """A dica de excluir pastas de ambiente virtual saiu da barra lateral (issue #41).

    `NON_PROJECT_FOLDERS` já exclui `.venv` sozinho, então a dica ensinava um passo
    inútil. Ela vivia num `st.sidebar.info`; a guarda é que a barra lateral não volte
    a instruir a ignorar ambiente virtual, em nenhuma das línguas.
    """
    app = _run(language)
    sidebar_text = " ".join(element.value for element in app.sidebar.info).lower()

    assert "virtual environment" not in sidebar_text
    assert "ambiente virtual" not in sidebar_text


def test_a_typed_garbage_lang_still_opens_the_app():
    """A URL é digitável: `?lang=klingon` abre em inglês em vez de derrubar a tela."""
    app = _run("klingon")

    assert app.exception == []
    assert app.header[0].value == translate("home.title", "en")


def test_the_selector_offers_every_language_in_its_own_name():
    """Cada opção no próprio idioma — o rótulo vem do arquivo, não de um mapa no código."""
    selector = _run().sidebar.selectbox[0]

    assert selector.options == [
        translate("language.name", language) for language in available_languages()
    ]


def test_choosing_a_language_writes_it_to_the_url():
    """O seletor não guarda a escolha em `session_state`: ele reescreve a URL.

    O `AppTest` devolve o parâmetro como lista, que é a forma crua do query string;
    o `st.query_params` da aplicação entrega o valor único.
    """
    app = _run()

    app.sidebar.selectbox[0].set_value("pt").run()

    assert app.query_params["lang"] == ["pt"]


def test_choosing_a_language_retranslates_the_screen():
    """Traduzir na renderização é o que evita rótulo velho até reexecutar a análise."""
    app = _run()

    app.sidebar.selectbox[0].set_value("pt").run()

    assert app.header[0].value == translate("home.title", "pt")
    assert app.sidebar.selectbox[0].label == translate("sidebar.language", "pt")


def test_the_selector_persists_its_choice_by_key():
    """A escolha vive numa `key` — é o que habilita o `on_change` a escrever `?lang=`.

    Sem `key`, a troca de língua dependia de um `st.rerun()` manual seguido de reafirmar
    todo o `session_state`, laço que estourava ao reatribuir `file_uploaded` (issue #53).
    O `on_change` lê a escolha desta chave e a copia para a URL.
    """
    app = _run()

    app.sidebar.selectbox[0].set_value("pt").run()

    assert app.session_state["language_choice"] == "pt"


def _sidebar_tree() -> ast.Module:
    """Árvore de `utils/sidebar.py` — o guarda estrutural lê o código, não a docstring."""
    source = (PROJECT_ROOT / "utils" / "sidebar.py").read_text(encoding="utf-8")
    return ast.parse(source)


def _has_self_assignment(tree: ast.Module) -> bool:
    """Há alguma atribuição `x = x` — o tell do laço que reafirmava o estado.

    Compara alvo e valor pela forma da AST, então pega `st.session_state[key] =
    st.session_state[key]` sem depender do nome da variável de iteração.
    """
    return any(
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and ast.dump(node.targets[0]) == ast.dump(node.value)
        for node in ast.walk(tree)
    )


def _calls_rerun(tree: ast.Module) -> bool:
    """Há alguma chamada `*.rerun(...)` no código — a docstring pode citá-la à vontade."""
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "rerun"
        for node in ast.walk(tree)
    )


def test_the_selector_no_longer_reasserts_the_whole_session_state():
    """O laço que reafirmava todas as chaves saiu — era ele que derrubava a home.

    Reafirmar `st.session_state[key] = st.session_state[key]` para toda chave alcançava
    `file_uploaded`, um widget em que o Streamlit proíbe atribuição por `session_state`.
    Com o `on_change` o rerun é interação real, carrega os widget_states, e o estado
    sobrevive pela compactação normal: o laço e o `st.rerun()` manual deixaram de existir
    (issue #53). A suíte é cega ao crash em si (`runtime.exists()` é falso sob `AppTest`),
    então este guarda estrutural é o que impede o laço de voltar.
    """
    tree = _sidebar_tree()

    assert not _has_self_assignment(tree)
    assert not _calls_rerun(tree)


def test_switching_language_leaves_no_label_from_the_old_one(visible_text, foreign_labels):
    """A tela sai inteira na língua nova, não metade em cada (issue #53).

    O `on_change` escreve `?lang=` antes do rerun que o Streamlit dispara, então a
    execução seguinte relê o parâmetro novo do início ao fim. Se o parâmetro só valesse
    daqui a uma execução, o corpo já renderizado sairia na língua antiga — o risco que a
    issue aponta.
    """
    app = _run("en")

    app.sidebar.selectbox[0].set_value("pt").run()

    assert visible_text(app).isdisjoint(foreign_labels("pt"))


@pytest.mark.parametrize("language", available_languages())
def test_the_home_screen_shows_no_label_from_another_language(
    language: str, visible_text, foreign_labels
):
    """A interface deixa de ser bilíngue: o seletor diz X e a tela responde em X.

    Era este o defeito — o seletor dizia "English" e a tela respondia "Informe o
    Projeto-Alvo", "Configurações", "Executar Análise Completa". Qualquer rótulo
    novo cravado no módulo em vez de resolvido por `t()` reabre o buraco, porque a
    outra língua continua tendo a chave e a tela não.
    """
    assert visible_text(_run(language)).isdisjoint(foreign_labels(language))


def _navigation_titles(language: str, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Títulos que o ponto de entrada passa a `st.navigation`, na língua pedida.

    `st.navigation` roda antes de qualquer página e o `AppTest` não expõe as páginas
    como elemento, então a leitura é feita no ponto onde o título é decidido — com o
    `main.py` de verdade rodando por trás.
    """
    captured: list[str] = []
    real_page = st.Page

    def spy(*args, **kwargs):
        captured.append(kwargs["title"])
        return real_page(*args, **kwargs)

    monkeypatch.setattr(st, "Page", spy)

    app = AppTest.from_file(ENTRY_POINT, default_timeout=30)
    app.query_params["lang"] = language
    app.run()

    assert app.exception == []
    return captured


@pytest.mark.parametrize("language", available_languages())
def test_the_navigation_titles_follow_the_url_language(
    language: str, monkeypatch: pytest.MonkeyPatch
):
    """A navegação lateral acompanha `?lang=` como o resto da tela.

    É o ponto mais fácil de esquecer: `st.navigation` roda em `main.py`, antes de
    qualquer página, e antes ficava com "Página Inicial" cravado enquanto o corpo da
    tela já falava inglês. A língua resolve ali porque `t()` lê de `st.query_params`,
    que já está disponível nesse ponto.
    """
    titles = _navigation_titles(language, monkeypatch)

    assert titles == [
        translate(key, language) for key in ("nav.home", "nav.report", "nav.loading")
    ]


def _with_target_project(language: str) -> AppTest:
    """Abre a home e carrega um Projeto-Alvo por diretório.

    O próprio ORÁCULO serve de Projeto-Alvo válido, então não é preciso fabricar um
    projeto de mentira só para ter fonte carregada.
    """
    app = _run(language)
    app.radio[0].set_value("directory").run()
    app.text_input[0].set_value(str(PROJECT_ROOT)).run()

    return app


def test_switching_language_keeps_the_loaded_target_project():
    """Trocar de língua é decisão de tela: não pode custar o trabalho já feito.

    A fonte e as pastas oferecidas vivem em `session_state`, e a língua vive na URL —
    é essa separação que faz o seletor não derrubar o Projeto-Alvo já carregado.
    """
    app = _with_target_project("en")
    assert app.session_state["archive"] is not None

    app.sidebar.selectbox[0].set_value("pt").run()

    assert app.session_state["archive"] is not None
    assert app.session_state["archive_is_valid"]
    assert app.header[0].value == translate("home.title", "pt")


def test_switching_language_keeps_the_checked_exclusions():
    """A Exclusão marcada é escolha do usuário sobre o projeto, não sobre o idioma."""
    app = _with_target_project("en")
    excluded = app.session_state["folder_list"][:2]
    app.multiselect[0].set_value(excluded).run()

    app.sidebar.selectbox[0].set_value("pt").run()

    assert app.session_state["ignore_folders"] == excluded


def test_the_ingestion_mode_survives_a_language_switch():
    """O modo escolhido é comparado por igualdade — o rótulo traduzido quebraria isso.

    `if mode == UPLOAD_MODE` decide qual campo aparece. Com o rótulo no lugar do
    valor, trocar de língua deixaria a comparação falsa e a tela voltaria sozinha
    para o campo de upload, perdendo o caminho já digitado.
    """
    app = _with_target_project("en")
    assert app.session_state["ingestion_mode"] == "directory"

    app.sidebar.selectbox[0].set_value("pt").run()

    assert app.session_state["ingestion_mode"] == "directory"
    assert app.text_input[0].label == translate("home.directory.label", "pt")


@pytest.mark.parametrize("language", available_languages())
def test_no_translated_label_is_stored_in_session_state(language: str):
    """Rótulo traduzido em `session_state` envelhece: ele sobreviveria à troca de língua.

    O estado guarda o que a análise produziu (`archive`, `ignore_folders`, ...), nunca
    o texto da tela.
    """
    app = _run(language)

    stored = {
        value for value in app.session_state.filtered_state.values() if isinstance(value, str)
    }

    assert stored.isdisjoint(load_locale(language).values())
