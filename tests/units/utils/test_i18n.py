"""
Testes da máquina de tradução da interface.

A língua é decisão de tela: ADR-0009 põe os rótulos em `locales/*.json`, resolvidos
por função própria e sem biblioteca de i18n. Aqui se guarda o que aquela decisão
promete — padrão inglês, chave ausente caindo para o inglês e paridade entre os
arquivos.
"""

import json
from pathlib import Path

import pytest

import utils.i18n
from utils.i18n import (
    DEFAULT_LANGUAGE,
    available_languages,
    current_language,
    load_locale,
    resolve_language,
    t,
    translate,
)

# Colhido na importação: parametrizar exige a lista antes da coleta, e é o que faz
# uma língua nova ser conferida sem que ninguém edite este arquivo.
TRANSLATED_LANGUAGES = [
    language for language in available_languages() if language != DEFAULT_LANGUAGE
]


@pytest.fixture
def half_translated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Uma tradução incompleta: `pt` esqueceu uma chave que o `en` tem.

    A paridade entre os arquivos reais impede montar este caso com eles — é
    justamente o que aquele teste existe para proibir. O buraco precisa ser
    fabricado aqui para provar o que acontece quando ele escapa.
    """
    (tmp_path / "en.json").write_text(
        json.dumps({"kept": "Kept", "forgotten": "Forgotten"}), encoding="utf-8"
    )
    (tmp_path / "pt.json").write_text(json.dumps({"kept": "Guardada"}), encoding="utf-8")
    monkeypatch.setattr(utils.i18n, "LOCALES_DIR", tmp_path)
    return tmp_path


def test_translate_resolves_a_key_in_the_requested_language():
    assert translate("sidebar.subtitle", "pt") == "Auditoria de Dependências Python"


def test_translate_falls_back_to_english_when_the_key_is_missing(half_translated: Path):
    """A tela fica bilingue por um instante — nunca quebrada, nunca com a chave crua."""
    assert translate("forgotten", "pt") == "Forgotten"


def test_the_repository_offers_english_and_portuguese():
    assert available_languages() == ["en", "pt"]


def test_a_new_language_is_a_new_file(half_translated: Path):
    """Mesma ideia dos registries `EXTRATORES`/`READERS` (ADR-0009): a língua entra
    pelo arquivo, sem `if` novo em `pages/`."""
    (half_translated / "de.json").write_text('{"kept": "Behalten"}', encoding="utf-8")

    assert available_languages() == ["de", "en", "pt"]


@pytest.mark.parametrize("language", TRANSLATED_LANGUAGES)
def test_every_language_has_exactly_the_keys_of_the_english(language: str):
    """Paridade: o mesmo conjunto de chaves dos dois lados.

    É o que transforma "esqueci de traduzir" em falha de build em vez de descoberta
    em produção (ADR-0009). O JSON não denuncia a assimetria sozinho como um `dict`
    ao lado do outro denunciaria; este teste é o que compra aquilo de volta.
    """
    assert set(load_locale(language)) == set(load_locale(DEFAULT_LANGUAGE))


def test_the_default_language_is_english():
    """Sem `?lang=` a interface abre em inglês: o público default deixou de ser a banca."""
    assert resolve_language(None) == "en"


def test_a_supported_language_is_honored():
    """É o que faz `?lang=pt` sobreviver ao refresh e o link ser compartilhável."""
    assert resolve_language("pt") == "pt"


@pytest.mark.parametrize("requested", ["", "xx", "PT", "en-US"])
def test_an_unsupported_language_falls_back_to_english(requested: str):
    """A URL é digitável por qualquer um: lixo em `?lang=` abre em inglês, não quebra."""
    assert resolve_language(requested) == "en"


def _query_params(monkeypatch: pytest.MonkeyPatch, params: dict[str, str]) -> None:
    """Finge a URL da requisição atual.

    A língua mora em `?lang=` e não em `session_state`: é isso que a faz sobreviver
    ao refresh e o link sair compartilhável já traduzido.
    """
    monkeypatch.setattr(utils.i18n.st, "query_params", params)


def test_the_language_comes_from_the_url(monkeypatch: pytest.MonkeyPatch):
    _query_params(monkeypatch, {"lang": "pt"})

    assert current_language() == "pt"


def test_a_url_without_lang_opens_in_english(monkeypatch: pytest.MonkeyPatch):
    _query_params(monkeypatch, {})

    assert current_language() == "en"


def test_t_translates_into_the_language_of_the_url(monkeypatch: pytest.MonkeyPatch):
    """`t` resolve na renderização: trocar a língua não depende de reexecutar a análise."""
    _query_params(monkeypatch, {"lang": "pt"})

    assert t("home.title") == translate("home.title", "pt")
