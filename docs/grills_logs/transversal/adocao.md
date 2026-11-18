# Adoção — restrições e calibragem de trabalho

Data: 2026-11-18

Sessão curta: o glossário (`CONTEXT.md`) e as decisões (`docs/adr/`, 13 ADRs) já
existiam, então o grill cobriu só o que não está escrito em outro lugar versionado —
o que não pode mudar no projeto e como o trabalho é fatiado. Este log é o backup
dessas respostas.

## Perguntas e respostas

**P: Qual comando roda a suíte de testes e qual instala as dependências numa árvore nova?**
R: `uv run pytest` e `uv sync`.

**P: O que não pode mudar no ORÁCULO?** (rascunho derivado do `CLAUDE.md` e dos ADRs)
R: Confirmado sem ajustes — ver lista final.

**P: A partir de quantas unidades tocadas uma issue vira plano de sub-tarefas?**
R: Sem limiar próprio; valem os defaults genéricos.

**P: Quais pastas são camadas para fatiar os commits?**
R: `core/` → `utils/` → `pages/`; `locales/` e `tests/` acompanham a mudança que usam/testam.

**P: Organizar os logs de grill por pasta?**
R: Sim — `docs/grills_logs/README.md` com as regras; este log em `transversal/`.

## Como ficou decidido

### Restrições

- Test command: `uv run pytest`
- Setup command: `uv sync`
- Python ≥3.11, gerenciado por uv; `uv.lock` versionado.
- Paradigma procedural (Regra 01 do enunciado): sem classes de domínio; Dependência é
  `TypedDict` (ADR-0011).
- Streamlit multipage via `st.navigation` como única interface.
- `core/` não importa `streamlit` nem conhece a língua da tela: código estável em inglês
  + dados (ADR-0010).
- i18n em JSON em `locales/`, sem biblioteca de i18n (ADR-0009).
- O CSV exportado é contrato; a língua é só da tela (ADR-0008).
- O enunciado (`docs/Enunciado.md`) é a fonte dos requisitos.
- A autoauditoria tem que passar: só declarar o que é importado de fato
  (`tests/integration/test_self_audit.py`).

### Calibragem de trabalho

- **Quebra de trabalho:** defaults genéricos.
- **Camadas:** 1. `core/` · 2. `utils/` · 3. `pages/`. `locales/` e `tests/` acompanham
  a mudança correspondente.
