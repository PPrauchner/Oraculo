"""
Módulo responsável pela exibição do relatório na interface gráfica.

Renderiza os dados analisados para o usuário utilizando Streamlit,
incluindo tabelas, métricas e opções de exportação.

Entrada:
- Dados do relatório

Saída:
- Interface visual interativa
"""

import streamlit as st
import plotly.express as px
from utils.sidebar import sidebar
from core.report.make_report import make_report
from core.report.export import export_to_csv, export_to_json
from utils.constants import GERADORES, MAPA_CORES_STATUS
import pandas as pd


def def_tabelas(dict: dict = GERADORES):
    """Renderiza as tabelas de dependências para cada status usando abas.
    Args:
        dict (dict, optional): Dicionário contendo as dependências agrupadas por status.
                               Padrão é GERADORES.
    """
    abas = st.tabs([key for key in dict.keys()])
    for i, (key, value) in enumerate(dict.items()):
        with abas[i]:
            def_tabela(make_report(value))


def def_tabela(report_list: dict = GERADORES):
    """Renderiza uma tabela de dependências usando Streamlit.
    Args:
        report_list (dict, optional): Lista de dicionários representando o relatório final.
                                       Padrão é GERADORES.
    """
    st.table(report_list)


def def_metricas(dict: dict = GERADORES):
    """Renderiza as métricas principais do relatório usando Streamlit.
    Args:
        dict (dict, optional): Dicionário contendo as dependências agrupadas por status.
                               Padrão é GERADORES.
    """
    colunas = st.columns(len(dict))
    for i, (key, value) in enumerate(dict.items()):
        colunas[i].metric(key, len(value))


def gerar_number_ok(dict: dict = GERADORES) -> int:
    """ "
    Calcula o número de dependências que estão "OK" (ou seja, que não possuem problemas) com base no dicionário de status.
    Args:
        dict (dict, optional): Dicionário contendo as dependências agrupadas por status.
                               Padrão é GERADORES.
    Returns:
        int: Número de dependências que estão "OK".

    """

    number_ok = len(dict.get("Todas as Dependências", []))
    for i, (key, value) in enumerate(dict.items()):
        if key != "Todas as Dependências":
            number_ok -= len(value)
    return number_ok


def def_saude(dict: dict = GERADORES):
    """Calcula e renderiza o índice de saúde do projeto com base no número de dependências "OK" em relação ao total de dependências.
    Args:
        dict (dict, optional): Dicionário contendo as dependências agrupadas por status.
                               Padrão é GERADORES.
    """

    st.write("")
    number_dependences = len(dict.get("Todas as Dependências", []))
    number_ok = gerar_number_ok(dict)

    saude_percent = int((number_ok) / number_dependences * 100)
    st.write(f"**Índice de Saúde do Projeto: {saude_percent}%**")
    st.progress(saude_percent / 100)


def def_donut(dados: dict = GERADORES):
    """ "Renderiza um gráfico de pizza (donut) para mostrar a proporção de dependências "OK" em relação aos outros status.
    Args:
        dados (dict, optional): Dicionário contendo as dependências agrupadas por status.
                               Padrão é GERADORES.


    """

    dict_donut = {
        "Status ": [" OK ✅"],
        "Quantidade ": [gerar_number_ok(dados)],
    }
    for key, value in dados.items():
        if key != "Todas as Dependências":
            dict_donut["Status "].append(key)
            dict_donut["Quantidade "].append(len(value))

    fig = px.pie(
        dict_donut,
        values="Quantidade ",
        names="Status ",
        hole=0.4,
        color_discrete_map=MAPA_CORES_STATUS,
    )

    fig.update_layout(
        width=310,
        height=310,
        margin=dict(t=0, b=0, l=0, r=0),
    )

    st.plotly_chart(fig, use_container_width=False)


@st.dialog("Configurações do Relatório")
def popup_exportacao(report_data: dict = GERADORES):
    """
    Exibe um diálogo para configurar a exportação do relatório.
    Args:
        report_data (dict, optional): Dicionário contendo os dados do relatório.
                                       Padrão é GERADORES.

    """
    if not report_data:
        st.warning("Não há dados para exportar.")
        return

    st.write("### 1. Selecione as colunas")
    todas_as_chaves = list(report_data.keys())
    chaves_selecionadas = []

    for chave in todas_as_chaves:
        nome_amigavel = chave.title()
        if st.checkbox(nome_amigavel, value=True, key=f"check_{chave}"):
            chaves_selecionadas.append(chave)

    st.divider()
    st.write("### 2. Formato do arquivo")
    formato = st.radio("Escolha como deseja baixar:", ["CSV", "JSON"], horizontal=True)

    if not chaves_selecionadas:
        st.error("Selecione pelo menos um campo.")
        return

    # --- PROCESSAMENTO DOS DADOS ---
    dados_filtrados = []

    for key, value in report_data.items():

        if key in chaves_selecionadas:

            for dictionary in value:
                dados_filtrados.append(dictionary)

    if formato == "CSV":
        arquivo_final = export_to_csv(dados_filtrados)
        mimetype = "text/csv"
        extensao = "csv"
    else:
        arquivo_final = export_to_json(dados_filtrados)
        mimetype = "application/json"
        extensao = "json"

    st.divider()

    st.download_button(
        label=f"Baixar Relatório .{extensao} 📥",
        data=arquivo_final,
        file_name=f"report_dp_auditor.{extensao}",
        mime=mimetype,
        use_container_width=True,
    )


sidebar()

st.title("📊 Relatório de Dependências")

if "file_uploaded" not in st.session_state:
    st.warning("⚠️ Nenhum dado encontrado. Volte para a Home e inicie a auditoria.")
    st.stop()
else:

    col_metricas, col_grafico = st.columns([3, 2], gap="large")

    with col_metricas:
        st.write("#### Principais Métricas")
        def_metricas(GERADORES)
        def_saude()

    with col_grafico:
        st.write("#### Proporção de Problemas detectados")
        def_donut()

    # Abas de visualização
    def_tabelas(GERADORES)

    # Centralizar o botão usando colunas
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Gerar Report 📋"):
            popup_exportacao(GERADORES)
