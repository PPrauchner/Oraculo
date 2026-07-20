"""
Comunicação com a API pública do PyPI.

Responsabilidades:
- Buscar, em uma única requisição a `/pypi/NAME/json`, os metadados de um pacote.
- Extrair dessa mesma resposta a versão mais recente, o Tamanho e a Idade de uma
  versão específica (ADR-0004), sem novas requisições.
"""

from datetime import date, datetime

import requests

from utils.constants import PYPI_BASE_URL

_TIMEOUT_SECONDS = 5

# As buscas correm em paralelo (32 threads). Uma Session compartilhada mantém o
# pool de conexões vivo entre elas, poupando o handshake TLS a cada pacote.
_SESSION = requests.Session()


def fetch_package_data(package_name: str) -> dict | None:
    """Busca os metadados de um pacote no PyPI em uma única requisição.

    Args:
        package_name: Nome de Distribuição do pacote (ex.: "pandas").

    Returns:
        O JSON de `/pypi/NAME/json` já parseado, ou ``None`` quando o pacote não
        existe no PyPI (privado/interno) ou há falha de rede — sem quebrar a
        análise dos demais pacotes.
    """
    url = f"{PYPI_BASE_URL}/{package_name}/json"

    try:
        response = _SESSION.get(url, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        print(f"Não foi possível checar o pacote '{package_name}' no PyPI. ({error})")
        return None


def get_latest_version(data: dict) -> str:
    """Extrai a versão mais recente dos metadados já buscados.

    Args:
        data: Metadados já buscados via `fetch_package_data`.

    Returns:
        A versão publicada, ou "" quando a resposta não a traz — uma resposta
        malformada é indisponibilidade de um pacote, não motivo para abortar a
        análise dos demais.
    """
    return data.get("info", {}).get("version", "")


def _release_files(data: dict, version: str) -> list[dict]:
    """Arquivos publicados de uma versão (vazio se a versão não existir)."""
    return data.get("releases", {}).get(version, [])


def get_release_size(data: dict, version: str) -> int | None:
    """Tamanho em bytes de uma versão: bytes do wheel, com sdist como fallback.

    Args:
        data: Metadados já buscados via `fetch_package_data`.
        version: Versão exata cujo Tamanho se quer (a Versão Usada).

    Returns:
        Os bytes de um wheel (`bdist_wheel`); na falta de wheel, os do sdist;
        ``None`` quando a versão não tem artefatos ou não existe na resposta.

    Um pacote com wheels por plataforma publica dezenas de artefatos da mesma
    versão, de tamanhos bem diferentes. A escolha é fixada pela ordem alfabética do
    nome do arquivo, não pela ordem em que o PyPI devolveu: o ADR-0004 exige que o
    mesmo pacote dê sempre o mesmo número, senão a série temporal da US-07 inventa
    variação que não houve.
    """
    files = _release_files(data, version)
    if not files:
        return None

    wheels = [f for f in files if f.get("packagetype") == "bdist_wheel"]
    sdists = [f for f in files if f.get("packagetype") == "sdist"]
    candidates = wheels or sdists or files
    chosen = min(candidates, key=lambda f: f.get("filename", ""))

    return chosen.get("size")


def _parse_upload_time(raw: str) -> date | None:
    """Converte o `upload_time` do PyPI (ISO, UTC ingênuo) em data."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "")).date()
    except ValueError:
        return None


def get_release_age_days(
    data: dict, version: str, today: date | None = None
) -> int | None:
    """Idade em dias de uma versão: hoje menos a data de publicação dela.

    A data de publicação da versão é o `upload_time` mais antigo entre seus
    artefatos (ADR-0004).

    Args:
        data: Metadados já buscados via `fetch_package_data`.
        version: Versão exata cuja Idade se quer (a Versão Usada).
        today: Data de referência; usa `date.today()` quando omitida.

    Returns:
        Dias inteiros desde a publicação, ou ``None`` quando a versão não existe
        ou não traz `upload_time`.
    """
    files = _release_files(data, version)
    upload_dates = [
        parsed
        for f in files
        if (parsed := _parse_upload_time(f.get("upload_time", ""))) is not None
    ]
    if not upload_dates:
        return None

    reference = today or date.today()
    return (reference - min(upload_dates)).days
