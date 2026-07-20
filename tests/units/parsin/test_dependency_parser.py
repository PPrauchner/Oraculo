from core.parsin.dependency_parser import parse_dependencies


def test_origem_sobrevive_a_normalizacao():
    """A Origem lida pelo reader precisa chegar à análise (ADR-0003)."""
    raw = [
        {"package": "streamlit", "used_version": "1.37.0", "Origem": "Production"},
        {"package": "ruff", "used_version": "0.6.0", "Origem": "Development"},
    ]

    result = parse_dependencies(raw)

    assert [dep["Origem"] for dep in result] == ["Production", "Development"]


def test_dependencia_sem_origem_e_tratada_como_producao():
    """Sem Origem declarada, o padrão conservador é Produção."""
    result = parse_dependencies([{"package": "pandas", "used_version": "3.0.1"}])

    assert result[0]["Origem"] == "Production"
