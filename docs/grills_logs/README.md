# Logs de grill

Registro das sessões de *grill* (entrevista que estressa um plano contra o domínio e as
decisões do projeto). Cada log é uma fotografia do momento em que foi escrito.

## Regras

- **Uma pasta por unidade do projeto** — um pacote de `core/` (`ingestion`, `parsin`,
  `analysis`, `pypi`, `report`), `pages`, `utils`. A pasta nasce com o primeiro grill
  da unidade; não há lista fechada.
- **`transversal/`** — o que toca mais de uma unidade, ou é manutenção do repositório.
- **`negocio/`** — divulgação, apresentação, propostas.
- **Releases:** uma linha `Releases: vX.Y.Z, ...` logo abaixo do título lista as
  releases que entregaram o que o grill decidiu. Sem ela, a decisão ainda não saiu.
- **O log não é fonte da verdade.** Na mesma pasta vale o mais recente; o que vale
  hoje está no código, nos ADRs (`docs/adr/`) e no `CONTEXT.md`.
- Logs anteriores a estas regras ficam onde estão, como registro histórico.
