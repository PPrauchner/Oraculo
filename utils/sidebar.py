"""
Módulo responsável pela sidebar da aplicação.

Define e renderiza a barra lateral utilizada em todas as páginas,
incluindo navegação e opções de configuração.

Entrada:
- Estado da aplicação

Saída:
- Componente visual reutilizável
"""

from utils.constants import SVG_LUPA
from utils.i18n import LANGUAGE_PARAM, available_languages, current_language, t, translate
from utils.theme import theme_color
import streamlit as st


def language_selector() -> None:
    """Oferece as línguas disponíveis e guarda a escolha na URL.

    Cada opção aparece na própria língua (`language.name`), então acrescentar um
    arquivo em `locales/` basta para a língua entrar aqui — sem `if` novo (ADR-0009).
    O widget não usa `key`: a língua mora em `?lang=`, e ter os dois guardando a
    mesma coisa criaria duas fontes da verdade que discordam no refresh.
    """
    languages = available_languages()
    current = current_language()

    chosen = st.selectbox(
        t("sidebar.language"),
        options=languages,
        index=languages.index(current),
        format_func=lambda language: translate("language.name", language),
    )

    if chosen != current:
        st.query_params[LANGUAGE_PARAM] = chosen

        # A barra lateral roda antes do corpo da página, então o `st.rerun()` abaixo
        # aborta o script antes de a página registrar seus widgets — e o Streamlit
        # descarta o estado de todo widget que não foi registrado na execução. Sem
        # reafirmar as chaves, trocar de idioma apagaria o Projeto-Alvo carregado e
        # as Exclusões marcadas: um seletor de aparência não pode custar o trabalho
        # já feito. Reatribuir marca a chave como posta pelo usuário, que é o que a
        # faz sobreviver.
        for key in list(st.session_state.keys()):
            st.session_state[key] = st.session_state[key]

        # Sem o rerun a tela sai metade em cada língua: o que já foi renderizado
        # acima leu o parâmetro antigo. Não há laço — depois do rerun a escolha e a
        # URL concordam, e a condição fica falsa.
        st.rerun()


def sidebar() -> None:
    """
    Função responsável por renderizar a barra lateral da aplicação.
    Ela exibe o título, uma descrição e uma seção de configurações onde o usuário pode selecionar pastas a serem ignoradas durante a análise de dependências.
    A função também desabilita a seleção de pastas quando o usuário está fora da página inicial.

    Args:
        pagina_atual (str, optional): Identificador da página atual para controle de estado. Defaults to "home".

    Returns:
        None

    """
    with st.sidebar:

        # A lupa herda esta cor via `currentColor`, então título e ícone saem da
        # mesma fonte — a cor primária da paleta.
        st.markdown(
            f'<h1 style="display: flex; align-items: center; color: {theme_color("primaryColor")}">{SVG_LUPA} ORÁCULO</h1>',
            unsafe_allow_html=True,
        )

        st.markdown(t("sidebar.subtitle"))

        language_selector()

        # Legenda, e não controle: o tema é do mecanismo nativo do Streamlit, que já
        # guarda a escolha por sessão no navegador do visitante. `theme.base` é
        # `scriptable = False`, então não há alternador próprio a oferecer aqui — o que
        # falta é dizer onde fica o que já existe. O caminho do menu (`Settings →
        # Theme`) fica em inglês nos dois locales de propósito: é o rótulo literal que
        # o Streamlit desenha na tela, e traduzi-lo apontaria para algo inexistente.
        st.caption(t("sidebar.theme_hint"))

        st.divider()

    st.sidebar.info(t("sidebar.tip"))
