"""
Módulo responsável por identificar dependências desatualizadas.

Realiza a comparação entre a versão utilizada no projeto e a versão
mais recente disponível no PyPI.

Entrada:
- Lista de dependências com versões atuais
- Dados obtidos da API do PyPI

Saída:
- Lista de dependências desatualizadas com suas versões
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from core.analysis.ghost_analizer import is_ghost
from core.pypi.pypi_client import (
    fetch_package_data,
    get_latest_version,
    get_release_age_days,
    get_release_size,
)
from packaging.version import InvalidVersion, parse as parse_version
from utils.constants import VERSION_UNAVAILABLE
from utils.types import Dependency


def _used_version(dep: Dependency) -> str:
    """Devolve a Versão Usada exatamente como o PyPI a publica, ou "" se indisponível.

    A Versão Usada já chega resolvida (Lock ou pin exato), então não há
    especificador a extrair — e extrair mutilaria versão válida: truncar o sufixo
    PEP 440 faria `2.0.0b1` virar a chave `2.0.0` e ler a release *errada* em
    `releases[]` (ADR-0004). O valor só é aceito se for uma versão PEP 440; "N/A"
    (Fantasma) e "N/D" contam como indisponível.

    Args:
        dep: Dependência com a chave 'Versão Usada'.

    Returns:
        A versão exata, ou "" quando não há Versão Usada conhecida.
    """
    raw = (dep.get("Versão Usada") or "").strip()

    try:
        parse_version(raw)
    except InvalidVersion:
        return ""

    return raw


def _set_size_and_age(dep: Dependency, data: dict, version: str | None) -> None:
    """Preenche 'Tamanho' e 'Idade' da versão de referência a partir dos metadados.

    Guarda os valores crus (bytes e dias inteiros) ou o sentinela de
    indisponibilidade; a formatação legível fica a cargo da camada de exibição.

    Args:
        dep: Dependência a preencher.
        data: Metadados já buscados no PyPI.
        version: Versão de referência (Versão Usada, ou a mais recente para
            Fantasmas). ``None`` quando não há referência (Versão Usada N/D de uma
            Dependência Declarada): Tamanho e Idade ficam indisponíveis, nunca 0.
    """
    if version is None:
        dep["Tamanho"] = VERSION_UNAVAILABLE
        dep["Idade"] = VERSION_UNAVAILABLE
        return

    size = get_release_size(data, version)
    age = get_release_age_days(data, version)
    dep["Tamanho"] = size if size is not None else VERSION_UNAVAILABLE
    dep["Idade"] = age if age is not None else VERSION_UNAVAILABLE


def _checar_dependencia(dep: Dependency) -> Dependency:
    """
    Consulta o PyPI para uma única dependência (um request) e preenche
    'Versão PyPI', 'Status', 'Tamanho' e 'Idade' diretamente no dicionário.

    Chamada em paralelo pelo ThreadPoolExecutor.

    Args:
        dep: Dicionário com pelo menos 'Pacote' e 'Versão Usada'.

    Returns:
        O mesmo dicionário com 'Versão PyPI', 'Status', 'Tamanho' e 'Idade'
        preenchidos.
    """
    data = fetch_package_data(dep["package"])
    versao_usada = _used_version(dep)
    pypi_version = get_latest_version(data) if data else ""

    if not pypi_version:
        # Pacote ausente do PyPI (privado/interno), falha de rede ou resposta sem
        # versão: indisponível, sem quebrar a análise dos demais pacotes.
        dep["Versão PyPI"] = "N/A"
        dep["status"]      = "Desconhecido"
        if not versao_usada:
            # Mesmo sentinela do caminho com PyPI: não conhecer a Versão Usada é
            # indisponibilidade, independente de o pacote existir no PyPI.
            dep["Versão Usada"] = VERSION_UNAVAILABLE
        _set_size_and_age(dep, data={}, version=None)
        return dep

    dep["Versão PyPI"] = pypi_version

    if not versao_usada:
        # Sem Lock e sem pin, a Versão Usada é desconhecida: não se afirma
        # "Atualizado" nem se copia a versão do PyPI (ADR-0002).
        dep["Versão Usada"] = VERSION_UNAVAILABLE
        dep["status"]       = VERSION_UNAVAILABLE
        # Fantasma não tem Declaração, logo não tem Origem (CONTEXT.md): usa a
        # versão mais recente como referência de Tamanho/Idade. Uma Dependência
        # Declarada sem Versão Usada não tem referência — fica indisponível.
        _set_size_and_age(dep, data, pypi_version if is_ghost(dep) else None)
    else:
        _set_size_and_age(dep, data, versao_usada)
        try:
            if parse_version(versao_usada) < parse_version(pypi_version):
                dep["status"] = "Desatualizado"
            else:
                dep["status"] = "Atualizado"
        except Exception:
            dep["status"] = "Versão Inválida"

    return dep


def analyze_dependency_status(dependencies: list[Dependency]) -> list[Dependency]:
    """
    Analisa o status de cada dependência comparando com o PyPI.

    Utiliza ThreadPoolExecutor para disparar as requisições em paralelo,
    reduzindo o tempo de execução de O(n) sequencial para próximo de O(1)
    em relação ao número de dependências.

    Args:
        dependencies: Lista de dicts com 'Pacote' e 'Versão Usada'.

    Returns:
        A mesma lista com 'Versão PyPI', 'Status', 'Tamanho' e 'Idade'
        preenchidos em cada item.
    """
    if not dependencies:
        return []

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(_checar_dependencia, dep): dep for dep in dependencies}

        for future in as_completed(futures):
            future.result()

    return dependencies