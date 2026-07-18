import pytest
from core.analysis.zombie_analizer import analyze_zombie_dependencies

def test_no_zombies():
    """Garante que não retorna zumbis se todas as declarações forem usadas."""
    declared = [{"Pacote": "pandas"}]
    imports = [{"Pacote": "pandas"}]
    assert analyze_zombie_dependencies(declared, imports) == []

def test_identify_zombies():
    """Identifica pacotes declarados mas não importados."""
    declared = [{"Pacote": "requests"}, {"Pacote": "numpy"}]
    imports = [{"Pacote": "requests"}]
    
    result = analyze_zombie_dependencies(declared, imports)
    assert len(result) == 1
    assert result[0]["Pacote"] == "numpy"

def test_zombie_normalization():
    """Verifica se lida com a diferença de hifen/underscore na detecção de zumbis."""
    declared = [{"Pacote": "scikit-learn"}]
    imports = [{"Pacote": "scikit_learn"}]
    assert analyze_zombie_dependencies(declared, imports) == []

def test_zombie_import_alias():
    """PyYAML declarado e 'import yaml' não deve virar zumbi (Alias de Import)."""
    declared = [{"Pacote": "PyYAML"}]
    imports = [{"Pacote": "yaml"}]
    assert analyze_zombie_dependencies(declared, imports) == []

@pytest.mark.parametrize(
    "distribution, import_name",
    [
        ("scikit-learn", "sklearn"),
        ("opencv-python", "cv2"),
        ("Pillow", "PIL"),
    ],
)
def test_zombie_common_import_aliases(distribution, import_name):
    """Mismatches comuns do ecossistema não geram zumbis."""
    declared = [{"Pacote": distribution}]
    imports = [{"Pacote": import_name}]
    assert analyze_zombie_dependencies(declared, imports) == []

def test_zombie_multiple_import_names():
    """Distribuição com vários Nomes de Import casa por qualquer um deles."""
    declared = [{"Pacote": "setuptools"}]
    imports = [{"Pacote": "pkg_resources"}]
    assert analyze_zombie_dependencies(declared, imports) == []