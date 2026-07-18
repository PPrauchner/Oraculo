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
            "Tamanho": 2 * 1024 * 1024,
            "Idade": 30,
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
            "Tamanho": "2.0 MB",
            "Idade": "30 dias",
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


def test_normalize_formats_tamanho_as_readable_units():
    """Tamanho cru (bytes) vira unidade legível (KB/MB) na tabela."""
    input_data = [
        {"Pacote": "big", "Tamanho": 2 * 1024 * 1024, "Origem": "Produção"},
        {"Pacote": "small", "Tamanho": 500 * 1024, "Origem": "Produção"},
    ]

    result = normalize(input_data)

    assert result[0]["Tamanho"] == "2.0 MB"
    assert result[1]["Tamanho"] == "500.0 KB"


def test_normalize_formats_idade_in_days():
    """Idade crua (dias inteiros) é exibida em dias."""
    input_data = [{"Pacote": "pkg", "Idade": 30, "Origem": "Produção"}]

    result = normalize(input_data)

    assert result[0]["Idade"] == "30 dias"


def test_normalize_tamanho_idade_indisponivel_pass_through():
    """Tamanho/Idade indisponíveis (N/D) permanecem N/D, nunca 0."""
    input_data = [
        {"Pacote": "pkg", "Tamanho": "N/D", "Idade": "N/D", "Origem": "Produção"}
    ]

    result = normalize(input_data)

    assert result[0]["Tamanho"] == "N/D"
    assert result[0]["Idade"] == "N/D"


def test_normalize_missing_tamanho_idade_defaults_indisponivel():
    """Sem Tamanho/Idade informados, exibe indisponível em vez de quebrar."""
    result = normalize([{"Pacote": "numpy", "Origem": "Produção"}])

    assert result[0]["Tamanho"] == "N/D"
    assert result[0]["Idade"] == "N/D"


def test_normalize_ghost_marks_reference_as_latest_version():
    """Fantasma (sem Origem) explicita que Tamanho/Idade são da versão mais recente."""
    ghost = [{"Pacote": "requests", "Tamanho": 1024 * 1024, "Idade": 5}]

    result = normalize(ghost)

    assert "última versão" in result[0]["Tamanho"]
    assert "última versão" in result[0]["Idade"]