"""
Testes da leitura do modo hospedado.

Publicado, o campo de caminho da home resolveria no servidor, não na máquina de quem
usa (ADR-0014). Quem liga o modo é a variável de ambiente `ORACULO_HOSTED` — no
Streamlit Community Cloud, uma chave raiz dos *Secrets* chega ao processo assim —,
então é só ela que se lê aqui.

Cada teste fixa ou apaga a variável: o ambiente de quem roda a suíte não pode mudar
o resultado.
"""

import pytest

from utils.hosting import HOSTED_VARIABLE, is_hosted


@pytest.mark.parametrize("value", ["true", "TRUE", "True", "1"])
def test_the_hosted_mode_turns_on(monkeypatch, value: str):
    monkeypatch.setenv(HOSTED_VARIABLE, value)

    assert is_hosted() is True


@pytest.mark.parametrize("value", ["false", "0", "", "yes", "on", "verdadeiro"])
def test_any_other_value_leaves_it_off(monkeypatch, value: str):
    """Só o que foi combinado liga: ligar por engano esconderia o modo diretório."""
    monkeypatch.setenv(HOSTED_VARIABLE, value)

    assert is_hosted() is False


def test_without_the_variable_the_mode_is_off(monkeypatch):
    """Execução local, sem configuração nenhuma: comportamento de sempre."""
    monkeypatch.delenv(HOSTED_VARIABLE, raising=False)

    assert is_hosted() is False


def test_surrounding_whitespace_does_not_matter(monkeypatch):
    """Um espaço colado no valor do painel não deve desligar a guarda."""
    monkeypatch.setenv(HOSTED_VARIABLE, " true ")

    assert is_hosted() is True
