import pytest
from core.analysis.zombie_analizer import analyze_zombie_dependencies
from utils.constants import ORIGIN_DEVELOPMENT, ORIGIN_PRODUCTION

def test_no_zombies():
    """Garante que não retorna zumbis se todas as declarações forem usadas."""
    declared = [{"package": "pandas"}]
    imports = [{"package": "pandas"}]
    assert analyze_zombie_dependencies(declared, imports) == []

def test_identify_zombies():
    """Identifica pacotes declarados mas não importados."""
    declared = [{"package": "requests"}, {"package": "numpy"}]
    imports = [{"package": "requests"}]
    
    result = analyze_zombie_dependencies(declared, imports)
    assert len(result) == 1
    assert result[0]["package"] == "numpy"

def test_zombie_normalization():
    """Verifica se lida com a diferença de hifen/underscore na detecção de zumbis."""
    declared = [{"package": "scikit-learn"}]
    imports = [{"package": "scikit_learn"}]
    assert analyze_zombie_dependencies(declared, imports) == []

def test_zombie_import_alias():
    """PyYAML declarado e 'import yaml' não deve virar zumbi (Alias de Import)."""
    declared = [{"package": "PyYAML"}]
    imports = [{"package": "yaml"}]
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
    declared = [{"package": distribution}]
    imports = [{"package": import_name}]
    assert analyze_zombie_dependencies(declared, imports) == []

def test_zombie_multiple_import_names():
    """Distribuição com vários Nomes de Import casa por qualquer um deles."""
    declared = [{"package": "setuptools"}]
    imports = [{"package": "pkg_resources"}]
    assert analyze_zombie_dependencies(declared, imports) == []

def test_development_origin_never_zombie():
    """Dependência de Desenvolvimento não importada não é Zumbi (ADR-0003).

    pytest é importado só em tests/ (uma Exclusão) e ruff/mypy não são
    importados por ninguém, mas nenhum pode virar Zumbi.
    """
    declared = [
        {"package": "pytest", "origin": ORIGIN_DEVELOPMENT},
        {"package": "ruff", "origin": ORIGIN_DEVELOPMENT},
        {"package": "mypy", "origin": ORIGIN_DEVELOPMENT},
    ]
    imports = []
    assert analyze_zombie_dependencies(declared, imports) == []

def test_production_origin_not_imported_is_zombie():
    """Dependência de Produção não importada continua sendo Zumbi."""
    declared = [{"package": "requests", "origin": ORIGIN_PRODUCTION}]
    imports = []
    result = analyze_zombie_dependencies(declared, imports)
    assert len(result) == 1
    assert result[0]["package"] == "requests"

def test_only_production_zombies_when_origins_mixed():
    """Com Produção e Desenvolvimento juntas, só a Produção não usada é Zumbi."""
    declared = [
        {"package": "requests", "origin": ORIGIN_PRODUCTION},
        {"package": "pytest", "origin": ORIGIN_DEVELOPMENT},
    ]
    imports = []
    result = analyze_zombie_dependencies(declared, imports)
    assert [dep["package"] for dep in result] == ["requests"]