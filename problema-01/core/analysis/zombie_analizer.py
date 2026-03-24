"""
Módulo responsável por identificar dependências zumbis.

Dependências zumbis são aquelas que estão declaradas no projeto,
mas não são utilizadas no código (não aparecem nos imports).

Entrada:
- Conjunto de dependências declaradas
- Conjunto de imports utilizados no código

Saída:
- Conjunto de dependências zumbis
"""
# --- IGNORE ---