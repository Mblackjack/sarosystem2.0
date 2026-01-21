# -*- coding: utf-8 -*-
import streamlit as st
import os
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide")

st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .titulo-custom { color: #960018; font-weight: bold; font-size: 1.5rem; }
    .area-download { border: 2px solid #960018; padding: 20px; text-align: center; border-radius: 10px; background-color: #ffffff; margin-top: 20px; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

try:
    classificador = ClassificadorDenuncias()
except Exception:
    st.error("Erro ao carregar sistema. Verifique a chave API nos Secrets.")
    st.stop()

st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.title("⚖️ Sistema SARO - MPRJ")
st.divider()

# --- TÓPICO 1: NOVO REGISTRO (Mantido) ---
with st.form("form_reg", clear_on_submit=True):
    st.markdown('<p class="titulo-custom">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    num_com = c1.text_input("Nº de Comunicação")
    num_mprj = c2.text_input("Nº MPRJ")
    endereco = st.text_input("Endereço Completo")
    denuncia = st.text_area("Descrição da Ouvidoria")
    
    f1, f2 = st.columns(2)
    responsavel = f1.radio("Responsável:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = f2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("REGISTRAR OUVIDORIA", use_container_width=True):
        if endereco and denuncia:
            with st.spinner("Classificando e salvando no Excel..."):
                st.session_state.resultado = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.success("✅ Registro realizado e adicionado ao arquivo!")
        else:
            st.error("Preencha os campos obrigatórios.")

# --- TÓPICO 2: CLASSIFICAÇÃO ATUAL (Mantido) ---
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown('<p class="titulo-custom">✅ Registro da Classificação Atual</p>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Empresa", res["Empresa"])
    col_b.metric("Tema", res["Tema"])
    col_c.metric("Município", res["Município"])
    st.markdown(f'<div class="resumo-box"><b>Resumo IA:</b> {res["Resumo"]}</div>', unsafe_allow_html=True)

st.divider()

# --- TÓPICO 3: REGISTRO DE OUVIDORIAS (ÁREA DO ARQUIVO) ---
st.markdown('<p class="titulo-custom">📊 Registro de Ouvidorias</p>', unsafe_allow_html=True)

excel_path = os.path.join(os.path.dirname(__file__), "Ouvidorias_SARO_Oficial.xlsx")

if os.path.exists(excel_path):
    with open(excel_path, "rb") as f:
        st.markdown('<div class="area-download">', unsafe_allow_html=True)
        st.markdown('Clique abaixo para baixar o arquivo Excel atualizado com todos os registros:')
        st.download_button(
            label="📂 BAIXAR ARQUIVO EXCEL: REGISTRO_OUVIDORIAS_SARO",
            data=f,
            file_name="Registro_Ouvidorias_SARO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("O arquivo Excel será gerado automaticamente após o primeiro registro.")

st.caption("SARO v2.0 | Ministério Público do Rio de Janeiro")
