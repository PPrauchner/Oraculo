import pytest
from core.analysis.ghost_analizer import analyze_ghost_dependencies

def test_no_ghost_dependencies():
    """Garante que não retorna fantasmas quando tudo está declarado."""
    declared = [{"Pacote": "requests"}, {"Pacote": "pandas"}]
    imports = [{"Pacote": "requests"}]
    
    # A função deve retornar uma lista vazia
    result = analyze_ghost_dependencies(declared, imports)
    assert result == []

def test_single_ghost_dependency():
    """Identifica quando um import não consta na lista de declarados."""
    declared = [{"Pacote": "requests"}]
    imports = [{"Pacote": "requests"}, {"Pacote": "streamlit"}]
    
    result = analyze_ghost_dependencies(declared, imports)
    
    # Deve retornar apenas o streamlit
    assert len(result) == 1
    assert result[0]["Pacote"] == "streamlit"

def test_normalization_dash_and_underscore():
    """Verifica se a normalização de '-' para '_' funciona corretamente."""
    # O código substitui '-' por '_' e coloca em lowercase
    declared = [{"Pacote": "django-rest-framework"}]
    imports = [{"Pacote": "django_rest_framework"}]
    
    result = analyze_ghost_dependencies(declared, imports)
    assert result == []

def test_case_insensitivity():
    """Garante que a comparação ignore diferenças de maiúsculas e minúsculas."""
    declared = [{"Pacote": "PyYAMl"}]
    imports = [{"Pacote": "pyyaml"}]
    
    result = analyze_ghost_dependencies(declared, imports)
    assert result == []

def test_empty_inputs():
    """Verifica o comportamento com listas vazias."""
    assert analyze_ghost_dependencies([], []) == []
    assert analyze_ghost_dependencies([], [{"Pacote": "numpy"}]) == [{"Pacote": "numpy"}]