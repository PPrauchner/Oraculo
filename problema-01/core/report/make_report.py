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


def make_report(list_analyzed: list) -> list[dict]:
    """
    Constrói um DataFrame consolidando os resultados das análises.

    Args:
        list_analyzed (list): Lista de dependências com seus resultados de análise.

    Returns:
        list[dict]: Lista de dicionários representando o relatório final.
    """

    rows = []

    for dep in list_analyzed:
        rows.append(
            {
                "Pacote": dep.get("name", "N/A"),
                "Versão Atual": dep.get("current_version", "N/A"),
                "Versão PyPI": dep.get("pypi_version", "N/A"),
                "Status": dep.get("status", "Desconhecido"),
            }
        )

    if not rows:
        return [
            {
                "Pacote": "N/A",
                "Versão Atual": "N/A",
                "Versão PyPI": "N/A",
                "Status": "N/A",
            }
        ]
    return rows
