"""
Testes do tema: a paleta única e sua leitura pelo código.

A paleta vive em `.streamlit/config.toml` — é ela a fonte da verdade das cores,
não um hex solto em Python. Estes testes cobrem o que dá para verificar sem olhar
a tela: que o arquivo existe e declara os dois modos, que as cores das Categorias
saem de tokens semânticos do Streamlit, e que cada cor da paleta tem contraste
suficiente contra o fundo claro *e* contra o fundo escuro — a mesma cor serve aos
dois modos, então precisa ser legível nos dois.
"""

import re
import tomllib
from pathlib import Path

import pytest

from utils.constants import STATUS_COLOR_TOKENS
from utils.theme import status_colors, theme_color

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / ".streamlit" / "config.toml"


def _load_config() -> dict:
    return tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_config_do_streamlit_existe_e_e_valido():
    """O tema mora em `.streamlit/config.toml` e é TOML válido."""
    assert CONFIG_PATH.is_file()
    assert "theme" in _load_config()


def test_config_declara_os_dois_modos():
    """O tema define claro e escuro explicitamente, sem depender do default."""
    theme = _load_config()["theme"]

    assert "light" in theme
    assert "dark" in theme


def _relative_luminance(hex_color: str) -> float:
    """Luminância relativa de uma cor (WCAG 2.1)."""
    raw = hex_color.lstrip("#")
    channels = [int(raw[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    """Razão de contraste entre duas cores (WCAG 2.1), de 1:1 a 21:1."""
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


# Acima do mínimo de 3:1 que a WCAG pede para elemento gráfico (a fatia do donut).
MIN_CONTRAST = 4.0


def test_cores_das_categorias_sao_legiveis_nos_dois_fundos():
    """Cada cor de Categoria contrasta com o fundo claro *e* com o escuro.

    A mesma cor serve aos dois modos, então não basta funcionar em um: uma cor
    clara demais some no branco, uma escura demais some no fundo escuro. Este é o
    teste que substitui o "conferir o contraste do gráfico" a olho.
    """
    theme = _load_config()["theme"]
    light_background = theme["light"]["backgroundColor"]
    dark_background = theme["dark"]["backgroundColor"]

    category_tokens = ["blueColor", "violetColor", "redColor", "greenColor"]

    for token in category_tokens:
        color = theme[token]
        assert _contrast_ratio(color, light_background) >= MIN_CONTRAST, (
            f"{token} ({color}) some no fundo claro"
        )
        assert _contrast_ratio(color, dark_background) >= MIN_CONTRAST, (
            f"{token} ({color}) some no fundo escuro"
        )


def test_texto_contrasta_com_o_proprio_fundo_em_cada_modo():
    """O texto de cada modo é legível sobre o fundo daquele modo."""
    theme = _load_config()["theme"]

    for mode in ("light", "dark"):
        palette = theme[mode]
        # 4.5:1 é o mínimo da WCAG para texto corrido.
        assert (
            _contrast_ratio(palette["textColor"], palette["backgroundColor"]) >= 4.5
        ), f"texto ilegivel no modo {mode}"


def test_token_resolve_na_cor_declarada_no_config():
    """`theme_color` devolve a cor que o config.toml declara para o token."""
    declared = _load_config()["theme"]

    assert theme_color("blueColor") == declared["blueColor"]
    assert theme_color("violetColor") == declared["violetColor"]


def test_token_ausente_da_paleta_falha_alto(monkeypatch):
    """Token que o config.toml não declara é erro, não cor silenciosa.

    Devolver `None` faria o gráfico cair no default do Plotly sem ninguém notar —
    exatamente o tipo de divergência que a paleta única veio resolver. Simula-se a
    linha sumindo do config.toml, que é como o defeito apareceria de verdade.
    """
    monkeypatch.setattr("utils.theme.st.get_option", lambda _name: None)

    with pytest.raises(KeyError):
        theme_color("blueColor")


def test_cores_das_categorias_saem_todas_da_paleta():
    """Toda Categoria do donut resolve numa cor concreta da paleta."""
    colors = status_colors()
    declared = _load_config()["theme"]

    assert set(colors) == set(STATUS_COLOR_TOKENS)
    for label, token in STATUS_COLOR_TOKENS.items():
        assert colors[label] == declared[token]


def test_nenhuma_cor_fixa_sobrou_no_codigo():
    """A paleta existe num lugar só: nenhum hex solto em `pages/` ou `utils/`.

    Eram três azuis diferentes espalhados por CSS ad-hoc (issue #39). Qualquer hex
    reintroduzido aqui é uma quarta paleta nascendo — a cor tem de vir de
    `theme_color`, que lê o config.toml.
    """
    offenders = {}

    for directory in ("pages", "utils"):
        for module in (PROJECT_ROOT / directory).glob("*.py"):
            source = module.read_text(encoding="utf-8")
            if found := re.findall(r"#[0-9A-Fa-f]{6}\b", source):
                offenders[f"{directory}/{module.name}"] = found

    assert offenders == {}
