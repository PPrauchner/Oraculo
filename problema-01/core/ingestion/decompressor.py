"""
Módulo responsável pela leitura de arquivos compactados (.zip).

Fornece funções para abrir, listar e acessar arquivos dentro de um
arquivo ZIP, sem necessidade de extração para o disco.

Entrada:
- Arquivo ZIP em formato de bytes

Saída:
- Objeto manipulável do ZIP (zip_ref)
- Lista de arquivos contidos no ZIP
- Conteúdo de arquivos específicos
"""
# --- IGNORE ---