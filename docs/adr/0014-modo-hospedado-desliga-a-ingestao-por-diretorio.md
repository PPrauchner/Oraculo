*[English version](0014-modo-hospedado-desliga-a-ingestao-por-diretorio.en.md)*

# Modo hospedado desliga a ingestão por diretório

Restringe o [ADR-0001](0001-ingestao-por-upload-e-por-diretorio.md). A ingestão por
diretório assume que o Streamlit roda na máquina do dev, então o caminho digitado
resolve lá. Publicado no Streamlit Community Cloud, o mesmo caminho resolve **no
servidor**: qualquer visitante poderia apontar para uma pasta do container (o
repositório do próprio app, a stdlib instalada) e lê-la pela auditoria.

**Decidido:** o ADR-0001 vale para execução local. Com o **modo hospedado** ligado, a
home oferece só o upload — sem rádio, sem campo de caminho — e não abre caminho
digitado nem quando o estado de sessão pede `ingestion_mode == "directory"`.

- O modo é ligado só pela variável de ambiente `ORACULO_HOSTED` (`true` ou `1`, sem
  diferenciar maiúsculas). No Streamlit Cloud, a chave raiz dos *Secrets* chega ao
  processo assim; o código não lê `st.secrets` e não depende de existir
  `.streamlit/secrets.toml`. Sem a variável, nada muda.
- A decisão é de apresentação: mora em `utils/hosting.py` e na home. `core/` não sabe
  onde roda, e `open_directory`, `list_paths` e `read_text` não mudam.
- A recusa mira o caminho digitado, não o tipo da fonte: upload e Projeto-Alvo em
  memória seguem o fluxo normal.

Rejeitado: detectar a hospedagem por heurística (hostname, caminho de montagem), que
falha em silêncio quando a plataforma muda; e esconder só o rádio, que deixaria o
estado de sessão reabrir a porta.
