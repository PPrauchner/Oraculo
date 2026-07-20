"""
Traduz o código de erro que `core/` devolve para a frase que o usuário lê.

Responsabilidades:
- Guardar o texto de cada código de erro de ingestão.
- Compor a frase final com os parâmetros do erro (`format_error`).

`core/` detecta o problema e o nomeia em inglês; a redação, a língua e o ícone são
decisão de quem renderiza (ADR-0010). Fica em `utils/` — e não dentro de uma página —
porque `home.py` e `loading.py` exibem os mesmos erros, e é aqui que a resolução por
`locales/*.json` (ADR-0009) vai entrar no lugar deste dicionário.
"""

from core.ingestion.source import IngestionError

# Texto de cada código de erro de `core/ingestion/`. Provisoriamente em português e
# em código; ADR-0009 move isto para `locales/en.json` e `locales/pt.json`.
ERROR_MESSAGES: dict[str, str] = {
    "empty_path": "Informe o caminho do diretório do Projeto-Alvo.",
    "directory_not_found": "Caminho não encontrado: {path}",
    "path_is_not_a_directory": "O caminho informado não é um diretório: {path}",
    "directory_not_readable": "Sem permissão de leitura em: {path}",
    "directory_read_failed": "Não foi possível ler o diretório: {reason}",
    "not_a_python_project": (
        "O caminho não parece um projeto Python: {path}\n"
        "Esperado, na raiz, um arquivo .py ou uma Declaração "
        "(pyproject.toml, requirements.txt, environment.yml)."
    ),
    "source_missing": "O Projeto-Alvo não foi processado corretamente.",
    "unsupported_source": (
        "Fonte do Projeto-Alvo não suportada.\n"
        "Informe um diretório local ou um archive (zip, tar.gz ou tar)."
    ),
    "project_read_failed": "Erro ao ler o Projeto-Alvo: {reason}",
    "missing_python_and_declaration": (
        "O Projeto-Alvo deve conter:\n"
        "  1. Pelo menos um arquivo .py\n"
        "  2. Arquivo de dependências (requirements.txt, pyproject.toml, "
        "environment.yml ou .lock)"
    ),
    "missing_python_files": (
        "Nenhum arquivo .py encontrado no Projeto-Alvo.\n"
        "Certifique-se de que o código-fonte está incluído e fora das Exclusões."
    ),
    "missing_declaration": (
        "Nenhum arquivo de dependências encontrado.\n"
        "Incluir um dos seguintes: requirements.txt, pyproject.toml, "
        "environment.yml ou .lock"
    ),
}


def format_error(error: IngestionError) -> str:
    """Compõe a frase de um erro devolvido por `core/`.

    Args:
        error: Par (código, parâmetros) como `core/ingestion/` o devolve.

    Returns:
        A frase a exibir. Código desconhecido volta cru e parâmetro faltando deixa
        o placeholder intacto: um erro de tradução não pode esconder o erro que o
        usuário precisa ver.
    """
    code, params = error
    template = ERROR_MESSAGES.get(code)

    if template is None:
        return code

    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template
