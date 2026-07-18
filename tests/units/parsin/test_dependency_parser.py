from core.parsin.dependency_parser import parse_dependencies


def test_origem_sobrevive_a_normalizacao():
    """A Origem lida pelo reader precisa chegar à análise (ADR-0003)."""
    raw = [
        {"Pacote": "streamlit", "Versão Usada": "1.37.0", "Origem": "Produção"},
        {"Pacote": "ruff", "Versão Usada": "0.6.0", "Origem": "Desenvolvimento"},
    ]

    result = parse_dependencies(raw)

    assert [dep["Origem"] for dep in result] == ["Produção", "Desenvolvimento"]


def test_dependencia_sem_origem_e_tratada_como_producao():
    """Sem Origem declarada, o padrão conservador é Produção."""
    result = parse_dependencies([{"Pacote": "pandas", "Versão Usada": "3.0.1"}])

    assert result[0]["Origem"] == "Produção"
