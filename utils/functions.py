"""
Stores function dictionaries (registries).

"""

def registrar(dicionario : dict,formato: str):
    def decorador(funcao):
        dicionario[formato] = funcao
        return funcao

    return decorador

EXTRATORES : dict = {}

READERS : dict = {}