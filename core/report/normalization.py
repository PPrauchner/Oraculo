"""
Módulo responsável pela construção do relatório final.

Organiza os dados provenientes da análise em uma estrutura adequada
para visualização e exportação (ex: DataFrame).

Entrada:
- Lista com todas as dependências
- Resultados das análises (zumbis, fantasmas, desatualizados)

Saída:
- Estrutura de dados organizada (ex: Dicionário)
"""

from utils.constants import VERSION_UNAVAILABLE

_BYTES_PER_KB = 1024
_BYTES_PER_MB = 1024 * 1024
_LATEST_VERSION_NOTE = "última versão"


def _format_size(size: object) -> str:
    """Formata o Tamanho cru (bytes) em unidade legível (KB/MB).

    Args:
        size: Bytes inteiros da Versão Usada, ou o sentinela de indisponibilidade.

    Returns:
        "X.Y MB" a partir de 1 MB, "X.Y KB" abaixo disso, ou "N/D" quando
        indisponível — nunca 0 para o caso indisponível.
    """
    if not isinstance(size, (int, float)):
        return VERSION_UNAVAILABLE

    if size >= _BYTES_PER_MB:
        return f"{size / _BYTES_PER_MB:.1f} MB"
    return f"{size / _BYTES_PER_KB:.1f} KB"


def _format_age(age: object) -> str:
    """Formata a Idade crua (dias inteiros) em texto legível.

    Args:
        age: Dias inteiros desde a publicação da Versão Usada, ou o sentinela de
            indisponibilidade.

    Returns:
        "N dia(s)", ou "N/D" quando indisponível.
    """
    if not isinstance(age, (int, float)):
        return VERSION_UNAVAILABLE

    days = int(age)
    return f"{days} dia" if days == 1 else f"{days} dias"


def _display_metric(raw: object, is_fantasma: bool, formatter) -> str:
    """Formata Tamanho/Idade e, para Fantasma, explicita que é da versão mais recente.

    Args:
        raw: Valor cru da métrica.
        is_fantasma: Se a dependência é Fantasma (sem Declaração/Versão Usada), caso
            em que a referência é a versão mais recente do PyPI.
        formatter: `_format_size` ou `_format_age`.

    Returns:
        Texto legível, anotado com "(última versão)" quando Fantasma e disponível.
    """
    display = formatter(raw)
    if is_fantasma and display != VERSION_UNAVAILABLE:
        display = f"{display} ({_LATEST_VERSION_NOTE})"
    return display


def normalize(list_analyzed: list) -> list[dict]:
    """
    Constrói um Dicionário consolidando os resultados das análises.

    Args:
        list_analyzed (list): Lista de dependências com seus resultados de análise.

    Returns:
        list[dict]: Lista de dicionários representando o relatório final.
    """

    rows = []

    for dep in list_analyzed:
        # Fantasma não tem Declaração, logo não tem Origem (CONTEXT.md): seu
        # Tamanho/Idade referem-se à versão mais recente, e a tabela o explicita.
        is_fantasma = "Origem" not in dep
        rows.append(
            {
                "Pacote": dep.get("Pacote", "N/A"),
                "Versão Usada": dep.get("Versão Usada", "N/A"),
                "Versão PyPI": dep.get("Versão PyPI", "N/A"),
                "Status": dep.get("Status", "Desconhecido"),
                "Tamanho": _display_metric(
                    dep.get("Tamanho", VERSION_UNAVAILABLE), is_fantasma, _format_size
                ),
                "Idade": _display_metric(
                    dep.get("Idade", VERSION_UNAVAILABLE), is_fantasma, _format_age
                ),
                "Origem": dep.get("Origem", "N/A"),
            }
        )

    if not rows:
        return [
            {
                "Pacote": "N/A",
                "Versão Usada": "N/A",
                "Versão PyPI": "N/A",
                "Status": "N/A",
                "Tamanho": "N/A",
                "Idade": "N/A",
                "Origem": "N/A",
            }
        ]
    return rows
