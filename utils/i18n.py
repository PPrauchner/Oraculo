"""
Resolve o rótulo que o usuário lê na língua escolhida.

Responsabilidades:
- Carregar os rótulos de `locales/<língua>.json`.
- Traduzir uma chave, caindo para o inglês quando ela falta na língua pedida.
- Ler da URL (`?lang=`) a língua da requisição atual.

A língua vive no query param, e não em `st.session_state`, por dois motivos: ela
sobrevive ao refresh e o link sai compartilhável já traduzido. Pelo mesmo motivo
nenhum rótulo traduzido é guardado no estado — `t` resolve na renderização, senão
trocar a língua mostraria rótulo velho até reexecutar a análise.
"""

import json
from pathlib import Path

import streamlit as st

LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"

# Inglês é o padrão: o trabalho já foi avaliado e o projeto agora serve de
# portfólio, então a banca deixou de ser o público default (ADR-0009).
DEFAULT_LANGUAGE = "en"

# Nome do query param que carrega a língua.
LANGUAGE_PARAM = "lang"


def available_languages() -> list[str]:
    """Línguas que a interface oferece, em ordem alfabética.

    Returns:
        Um código por arquivo em `locales/`. Suportar uma língua nova é acrescentar
        o arquivo — nenhum código muda (ADR-0009).
    """
    return sorted(locale_file.stem for locale_file in LOCALES_DIR.glob("*.json"))


def resolve_language(requested: str | None) -> str:
    """Decide em que língua a interface fala.

    Args:
        requested: Língua pedida — na prática, o que veio em `?lang=`. `None` quando
            o parâmetro não está na URL.

    Returns:
        A língua pedida, se houver arquivo para ela; inglês em qualquer outro caso.
        A URL é digitável, então valor desconhecido abre em inglês em vez de derrubar
        a tela.
    """
    if requested is not None and requested in available_languages():
        return requested

    return DEFAULT_LANGUAGE


def load_locale(language: str) -> dict[str, str]:
    """Lê os rótulos de uma língua.

    Args:
        language: Código da língua, o nome do arquivo em `locales/` sem extensão.

    Returns:
        Os rótulos daquela língua, ou vazio se ela não tem arquivo.
    """
    locale_file = LOCALES_DIR / f"{language}.json"

    if not locale_file.is_file():
        return {}

    return json.loads(locale_file.read_text(encoding="utf-8"))


def translate(key: str, language: str) -> str:
    """Devolve o rótulo de uma chave na língua pedida.

    Args:
        key: Identificador do rótulo, como está em `locales/*.json`.
        language: Código da língua desejada.

    Returns:
        O rótulo na língua pedida; o inglês quando a chave falta nela. Chave que
        falta também no inglês volta crua: é bug de quem chamou, e esconder isso
        deixaria a tela vazia sem dizer por quê. O teste de paridade impede que a
        primeira queda vire rotina, e o inglês completo, que a segunda aconteça.
    """
    translated = load_locale(language).get(key)

    if translated is not None:
        return translated

    return load_locale(DEFAULT_LANGUAGE).get(key, key)


def current_language() -> str:
    """Língua da requisição atual, lida de `?lang=` na URL."""
    return resolve_language(st.query_params.get(LANGUAGE_PARAM))


def t(key: str) -> str:
    """Traduz uma chave na língua da requisição atual.

    Args:
        key: Identificador do rótulo, como está em `locales/*.json`.

    Returns:
        O rótulo pronto para a tela. Chamar na hora de renderizar, nunca guardar o
        resultado em `st.session_state`: o rótulo guardado envelhece quando o
        usuário troca de língua.
    """
    return translate(key, current_language())
