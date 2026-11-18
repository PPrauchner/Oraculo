"""
Ferramentas comuns a toda a suíte.

Responsabilidades:
- Isolar a suíte do modo hospedado de quem a roda.
"""

import pytest

from utils.hosting import HOSTED_VARIABLE


@pytest.fixture(autouse=True)
def _local_execution_by_default(monkeypatch):
    """Toda execução de teste começa local, com `ORACULO_HOSTED` ausente.

    Quem roda a suíte numa máquina com o modo hospedado ligado veria a home sem o
    modo diretório, e os testes de ingestão dupla quebrariam por causa do ambiente,
    não do código (ADR-0014). O teste que precisa do modo hospedado o liga sozinho.
    """
    monkeypatch.delenv(HOSTED_VARIABLE, raising=False)
