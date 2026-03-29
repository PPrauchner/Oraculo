"""
Módulo responsável por identificar dependências desatualizadas.

Realiza a comparação entre a versão utilizada no projeto e a versão
mais recente disponível no PyPI.

Entrada:
- Lista de dependências com versões atuais
- Dados obtidos da API do PyPI

Saída:
- Lista de dependências desatualizadas com suas versões
"""
from core.pypi.pypi_client import get_latest_version
from typing import Dict, Any, List

def analyze_outdated_dependencies(normalized_dependencies: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Analisa um conjunto de dependências e verifica seus status de atualização no PyPI.
    
    Args:
        normalized_dependencies (Dict[str, Any]): Dicionário contendo os pacotes 
            e suas versões locais, proveniente do módulo de normalização.
            Ex: {"pandas": {"version": "==1.0.0"}}
            
    Returns:
        Dict[str, List[Dict[str, str]]]: Um dicionário contendo três listas categorizadas:
            - 'up_to_date': pacotes que estão na versão mais recente.
            - 'outdated': pacotes com versão inferior à do PyPI.
            - 'unknown': pacotes não encontrados no PyPI ou com erro de verificação.
    """
    results = {
        "outdated": [],
        "up_to_date": [],
        "unknown": []
    }
    
    for package_name, info in normalized_dependencies.items():
        installed_version = info.get('version', '')
        
        clean_version = installed_version.replace("=", "").replace(">", "").replace("<", "").replace("~", "").strip()
        
        latest_version = get_latest_version(package_name)
        
        if latest_version:
            package_info = {
                "package": package_name,
                "current_version": clean_version,
                "new_version": latest_version
            }
            
            if clean_version != latest_version:
                results["outdated"].append(package_info)
            else:
                results["up_to_date"].append(package_info)
        else:
            results["unknown"].append({
                "package": package_name,
                "current_version": clean_version
            })
            
    return results