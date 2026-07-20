"""
Ritmo vertical e largura de leitura da aplicação, num único ponto.

O Streamlit não expõe o espaçamento do contêiner de bloco de forma declarativa —
`st.set_page_config(layout=...)` escolhe entre estreito e largo, e nada mais. Por
isso aqui existe uma folha de estilo, que a issue #39 baniu das páginas. A diferença
é estrutural, e não de intenção:

- **Ponto único**: declarada aqui e aplicada uma vez em `main.py`, para a aplicação
  inteira — não um bloco por página, que foi o defeito removido.
- **Somente layout**: espaçamento, largura e centragem. Nenhuma cor, nenhum hex,
  nenhuma família tipográfica; a cor continua saindo inteira de
  `.streamlit/config.toml`, que segue sendo a fonte da verdade.
- **Sem seletor frágil**: `.block-container` é classe pública do Streamlit;
  `data-testid` é detalhe interno, que muda de versão para versão sem aviso.

Responsabilidades:
- Declarar a folha de estilo de layout da aplicação.
- Aplicá-la uma vez por execução de página.
"""

import streamlit as st

# O padrão do Streamlit reserva ~6rem acima do primeiro elemento, espaço pensado para
# a barra de ferramentas flutuante. Numa tela de notebook isso empurra os controles
# para fora da primeira dobra antes de o usuário ter feito qualquer coisa.
CONTENT_TOP_PADDING = "3rem"

# `layout="wide"` tira o teto de largura, e sem teto o corpo acompanha o monitor: num
# ultrawide as duas colunas da tela inicial se afastam a ponto de o olho perder a
# linha entre o rótulo e o campo. O valor é fixo de propósito — em porcentagem ele
# voltaria a crescer junto com a tela, que é o defeito, não a correção.
READING_MAX_WIDTH = "1100px"

LAYOUT_STYLESHEET = f"""<style>
.block-container {{
    padding-top: {CONTENT_TOP_PADDING};
    max-width: {READING_MAX_WIDTH};
    margin-left: auto;
    margin-right: auto;
}}
</style>"""


def apply_layout() -> None:
    """Aplica o ritmo vertical e a largura de leitura da aplicação.

    Chamar uma vez, no ponto de entrada, antes de a página rodar: a folha vale para
    todas as páginas de uma vez, e repetir a chamada página a página seria justamente
    o CSS espalhado que a issue #39 removeu.
    """
    st.html(LAYOUT_STYLESHEET)
