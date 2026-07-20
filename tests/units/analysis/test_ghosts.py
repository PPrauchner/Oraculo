import pytest
from core.analysis.ghost_analizer import analyze_ghost_dependencies, is_ghost
from core.analysis.zombie_analizer import analyze_zombie_dependencies

def test_no_ghost_dependencies():
    """Garante que não retorna fantasmas quando tudo está declarado."""
    declared = [{"package": "requests"}, {"package": "pandas"}]
    imports = [{"package": "requests"}]
    
    # A função deve retornar uma lista vazia
    result = analyze_ghost_dependencies(declared, imports)
    assert result == []

def test_single_ghost_dependency():
    """Identifica quando um import não consta na lista de declarados."""
    declared = [{"package": "requests"}]
    imports = [{"package": "requests"}, {"package": "streamlit"}]
    
    result = analyze_ghost_dependencies(declared, imports)
    
    # Deve retornar apenas o streamlit
    assert len(result) == 1
    assert result[0]["package"] == "streamlit"

def test_normalization_dash_and_underscore():
    """Verifica se a normalização de '-' para '_' funciona corretamente."""
    # O código substitui '-' por '_' e coloca em lowercase
    declared = [{"package": "django-rest-framework"}]
    imports = [{"package": "django_rest_framework"}]
    
    result = analyze_ghost_dependencies(declared, imports)
    assert result == []

def test_case_insensitivity():
    """Garante que a comparação ignore diferenças de maiúsculas e minúsculas."""
    declared = [{"package": "PyYAMl"}]
    imports = [{"package": "pyyaml"}]
    
    result = analyze_ghost_dependencies(declared, imports)
    assert result == []

def test_empty_inputs():
    """Verifica o comportamento com listas vazias."""
    assert analyze_ghost_dependencies([], []) == []
    assert analyze_ghost_dependencies([], [{"package": "numpy"}]) == [{"package": "numpy"}]

def test_ghost_import_alias():
    """'import yaml' com PyYAML declarado não deve virar fantasma (Alias de Import)."""
    declared = [{"package": "PyYAML"}]
    imports = [{"package": "yaml"}]
    assert analyze_ghost_dependencies(declared, imports) == []

@pytest.mark.parametrize(
    "distribution, import_name",
    [
        ("scikit-learn", "sklearn"),
        ("opencv-python", "cv2"),
        ("Pillow", "PIL"),
    ],
)
def test_ghost_common_import_aliases(distribution, import_name):
    """Mismatches comuns do ecossistema não geram fantasmas."""
    declared = [{"package": distribution}]
    imports = [{"package": import_name}]
    assert analyze_ghost_dependencies(declared, imports) == []

def test_ghost_multiple_import_names():
    """Distribuição com vários Nomes de Import cobre todos eles."""
    declared = [{"package": "setuptools"}]
    imports = [{"package": "setuptools"}, {"package": "pkg_resources"}]
    assert analyze_ghost_dependencies(declared, imports) == []
def test_namespace_compartilhado_nao_e_alias():
    """`google` é namespace compartilhado, não Alias de protobuf.

    Mapeá-lo faria um projeto que importa `google.cloud.storage` "usar" um
    protobuf declarado e ocioso — falso negativo na US-03, o inverso do que a
    tabela de Aliases resolve.
    """
    declared = [{"package": "protobuf", "Origem": "Production"}]
    imports = [{"package": "google"}]

    assert analyze_zombie_dependencies(declared, imports) == declared


def test_is_ghost_reconhece_origem_ausente_e_origem_n_a():
    """Fantasma se identifica pela falta de Origem, na análise e na exibição.

    Os analisadores devolvem o Fantasma sem a chave; relatório e exportação
    preenchem "N/A". As duas formas precisam responder igual, senão a mesma
    dependência muda de categoria conforme a etapa do pipeline.
    """
    assert is_ghost({"package": "requests"})
    assert is_ghost({"package": "requests", "Origem": "N/A"})
    assert not is_ghost({"package": "requests", "Origem": "Production"})
    assert not is_ghost({"package": "ruff", "Origem": "Development"})
