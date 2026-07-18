import pytest
from core.report.normalization import normalize

def test_normalize_with_valid_data():
    """Verifica se a lista de dicionários é montada corretamente com dados válidos."""
    input_data = [
        {
            "Pacote": "pandas",
            "Versão Usada": "1.5.0",
            "Versão PyPI": "2.0.0",
            "Status": "Desatualizado",
            "Origem": "Produção",
            "Extra": "Deveria ser ignorado"
        }
    ]

    expected = [
        {
            "Pacote": "pandas",
            "Versão Usada": "1.5.0",
            "Versão PyPI": "2.0.0",
            "Status": "Desatualizado",
            "Origem": "Produção",
        }
    ]

    result = normalize(input_data)
    assert result == expected
    assert "Extra" not in result[0]

def test_normalize_with_missing_keys():
    """Verifica se o código lida com dicionários incompletos usando 'N/A'."""
    input_data = [{"Pacote": "numpy"}] # Faltam versões e status
    
    result = normalize(input_data)
    
    assert result[0]["Versão Usada"] == "N/A"
    assert result[0]["Status"] == "Desconhecido"

def test_normalize_empty_list():
    """Verifica o retorno padrão quando a lista de entrada está vazia."""
    result = normalize([])
    
    assert len(result) == 1
    assert result[0]["Pacote"] == "N/A"
    assert result[0]["Status"] == "N/A"

def test_normalize_multiple_items():
    """Garante que a função processa múltiplos itens na lista."""
    input_data = [
        {"Pacote": "pkg1", "Status": "OK"},
        {"Pacote": "pkg2", "Status": "Erro"}
    ]

    result = normalize(input_data)
    assert len(result) == 2
    assert result[0]["Pacote"] == "pkg1"
    assert result[1]["Pacote"] == "pkg2"

def test_normalize_surfaces_origin():
    """O relatório distingue Produção de Desenvolvimento expondo a Origem."""
    input_data = [
        {"Pacote": "requests", "Origem": "Produção"},
        {"Pacote": "pytest", "Origem": "Desenvolvimento"},
    ]

    result = normalize(input_data)

    assert result[0]["Origem"] == "Produção"
    assert result[1]["Origem"] == "Desenvolvimento"

def test_normalize_missing_origin_defaults_na():
    """Sem Origem informada, o relatório mostra 'N/A' em vez de quebrar."""
    result = normalize([{"Pacote": "numpy"}])

    assert result[0]["Origem"] == "N/A"