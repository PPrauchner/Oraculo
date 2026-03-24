"""
Módulo responsável pela normalização de dependências.

Padroniza nomes de pacotes e versões para garantir comparações corretas
entre dependências declaradas e imports utilizados.

Exemplo:
- "Flask" → "flask"
- "flask==2.0.0" → "flask"

Entrada:
- Nomes de dependências (strings)

Saída:
- Nomes normalizados
"""
# --- IGNORE ---