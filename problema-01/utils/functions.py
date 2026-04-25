"""
Módulo responsável por armazenar diconários de funções

"""

def registrar(dicionario : dict,formato: str):
    def decorador(funcao):
        dicionario[formato] = funcao
        return funcao

    return decorador

EXTRATORES : dict = {}

READERS : dict = {}