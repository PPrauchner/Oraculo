import pytest
from core.analysis.ghost_analizer import analyze_ghost_dependencies, is_ghost
from core.analysis.zombie_analizer import analyze_zombie_dependencies

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

def test_ghost_import_alias():
    """'import yaml' com PyYAML declarado não deve virar fantasma (Alias de Import)."""
    declared = [{"Pacote": "PyYAML"}]
    imports = [{"Pacote": "yaml"}]
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
    declared = [{"Pacote": distribution}]
    imports = [{"Pacote": import_name}]
    assert analyze_ghost_dependencies(declared, imports) == []

def test_ghost_multiple_import_names():
    """Distribuição com vários Nomes de Import cobre todos eles."""
    declared = [{"Pacote": "setuptools"}]
    imports = [{"Pacote": "setuptools"}, {"Pacote": "pkg_resources"}]
    assert analyze_ghost_dependencies(declared, imports) == []
def test_namespace_compartilhado_nao_e_alias():
    """`google` é namespace compartilhado, não Alias de protobuf.

    Mapeá-lo faria um projeto que importa `google.cloud.storage` "usar" um
    protobuf declarado e ocioso — falso negativo na US-03, o inverso do que a
    tabela de Aliases resolve.
    """
    declared = [{"Pacote": "protobuf", "Origem": "Production"}]
    imports = [{"Pacote": "google"}]

    assert analyze_zombie_dependencies(declared, imports) == declared


def test_is_ghost_reconhece_origem_ausente_e_origem_n_a():
    """Fantasma se identifica pela falta de Origem, na análise e na exibição.

    Os analisadores devolvem o Fantasma sem a chave; relatório e exportação
    preenchem "N/A". As duas formas precisam responder igual, senão a mesma
    dependência muda de categoria conforme a etapa do pipeline.
    """
    assert is_ghost({"Pacote": "requests"})
    assert is_ghost({"Pacote": "requests", "Origem": "N/A"})
    assert not is_ghost({"Pacote": "requests", "Origem": "Production"})
    assert not is_ghost({"Pacote": "ruff", "Origem": "Development"})
