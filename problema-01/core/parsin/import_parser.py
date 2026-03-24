"""
Módulo responsável por extrair imports do código-fonte.

Analisa arquivos Python utilizando AST (Abstract Syntax Tree)
para identificar dependências realmente utilizadas no código.

Entrada:
- Código-fonte Python (.py)

Saída:
- Conjunto de módulos/imports utilizados
"""
# --- IGNORE ---