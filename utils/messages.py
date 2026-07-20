"""
Traduz o código de erro que `core/` devolve para a frase que o usuário lê.

Responsabilidades:
- Nomear a chave de locale de um código de erro (`error_key`).
- Compor a frase final com os parâmetros do erro (`format_error`).

`core/` detecta o problema e o nomeia em inglês; a redação, a língua e o ícone são
decisão de quem renderiza (ADR-0010). O texto mora em `locales/*.json`, junto com o
resto da tela (ADR-0009): existe um caminho de tradução só, então o seletor de língua
alcança o erro como alcança qualquer outro rótulo. Fica em `utils/` — e não dentro de
uma página — porque `home.py` e `loading.py` exibem os mesmos erros.
"""

from core.ingestion.source import IngestionError
from utils.i18n import t

# Namespace dos códigos de erro dentro do locale. Sem ele, um código vindo de `core/`
# poderia colidir com a chave de um rótulo de tela.
ERROR_KEY_PREFIX = "error."


def error_key(code: str) -> str:
    """Chave de locale correspondente a um código de erro de `core/`.

    Args:
        code: Código estável em inglês, como `core/ingestion/` o devolve.

    Returns:
        A chave a procurar em `locales/*.json`.
    """
    return f"{ERROR_KEY_PREFIX}{code}"


def format_error(error: IngestionError) -> str:
    """Compõe a frase de um erro devolvido por `core/`, na língua da tela.

    Args:
        error: Par (código, parâmetros) como `core/ingestion/` o devolve.

    Returns:
        A frase a exibir. Código desconhecido volta cru e parâmetro faltando deixa
        o placeholder intacto: um erro de tradução não pode esconder o erro que o
        usuário precisa ver.
    """
    code, params = error
    key = error_key(code)
    template = t(key)

    # `t` devolve a própria chave quando ela falta em todas as línguas. Aqui isso
    # significa código sem tradução — e o que o usuário vê então é o código, que ao
    # menos é pesquisável, nunca o identificador de locale, que não diz nada.
    if template == key:
        return code

    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template
