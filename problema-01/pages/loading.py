"""
Módulo responsável pela interface de carregamento.

Exibe feedback visual durante o processamento da análise,
como spinners, barras de progresso e status das etapas.

Entrada:
- Estado do processamento

Saída:
- Feedback visual para o usuário
"""

import time
import streamlit as st
from utils_gui.sidebar import sidebar

st.set_page_config(page_title="Baita -Auditor - Analisando", layout="wide")
sidebar()


def run_tasks():
    """Executa as tarefas de backend e retorna a lista de funções."""
    return [
        lambda: (
            time.sleep(1.0)
            if st.session_state.get("file_uploaded")
            else st.error("Arquivo não encontrado!") or st.stop()
        ),
        lambda: time.sleep(1.5),  # scan_source
        lambda: time.sleep(2.0),  # query_pypi
        lambda: time.sleep(1.2),  # cross_reference
        lambda: time.sleep(1.0),  # calculate_metrics
    ]


def render_interface():
    st.markdown(
        """
        <style>
        .stApp { background: radial-gradient(circle at center, #1a3a3a 0%, #0e1117 70%); }
        .main-loader { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; color: white; font-family: 'Inter', sans-serif; }
        .loader-ring { width: 100px; height: 100px; border: 8px solid rgba(255,255,255,0.1); border-top: 8px solid #3498db; border-right: 8px solid #2ecc71; border-radius: 50%; animation: spin 1.5s linear infinite; margin-bottom: 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .step-list { font-family: 'Courier New', monospace; line-height: 1.8; text-align: left; width: 450px; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-loader"><div class="loader-ring"></div><div style="font-size:2rem; font-weight:bold; margin-bottom:20px;">Analysis in Progress...</div>',
        unsafe_allow_html=True,
    )

    list_placeholder = st.empty()
    steps_labels = [
        "1. Reading pyproject.toml...",
        "2. Scanning source code (ignoring folders)...",
        "3. Querying PyPI for package metadata...",
        "4. Cross-referencing imports...",
        "5. Calculating age and size...",
    ]

    tasks = run_tasks()

    for i, task in enumerate(tasks):
        html = '<div class="main-loader"><div class="step-list">'
        for j, label in enumerate(steps_labels):
            color = "#4CAF50" if j < i else ("#5dade2" if j == i else "#ffffff")
            opacity = "1" if j <= i else "0.3"
            cursor = " ▌" if j == i else (" ✅" if j < i else "")
            html += f'<div style="color:{color}; opacity:{opacity}; font-weight:{"bold" if j==i else "normal"}">{label}{cursor}</div>'
        html += "</div></div>"

        list_placeholder.markdown(html, unsafe_allow_html=True)
        task()

    st.markdown("</div>", unsafe_allow_html=True)
    time.sleep(0.5)
    st.switch_page("pages/report.py")


if __name__ == "__main__":
    render_interface()
