# -*- coding: utf-8 -*-
import streamlit as st
import os
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide")

st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .titulo-custom { color: #960018; font-weight: bold; font-size: 1.5rem; }
    .area-link { border: 2px dashed #960018; padding: 20px; text-align: center; border-radius: 10px; background-color: #fffafa; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

try:
    classificador = ClassificadorDenuncias()
except Exception:
    st.error("Erro ao iniciar. Verifique a GOOGLE_API_KEY nos Secrets.")
    st.stop()

st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.title("⚖️ Sistema SARO - MPRJ")

# --- NOVO REGISTRO ---
with st.form("form_registro", clear_on_submit=True):
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
            with st.spinner("Classificando..."):
                st.session_state.resultado = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.success("✅ Registro realizado com sucesso!")
        else:
            st.error("Preencha os campos obrigatórios.")

# --- CLASSIFICAÇÃO ATUAL ---
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown('<p class="titulo-custom">✅ Registro da Classificação Atual</p>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Empresa", res["Empresa"])
    col_b.metric("Tema", res["Tema"])
    col_c.metric("Município", res["Município"])
    st.write(f"**🏛️ Promotoria:** {res['Promotoria']}")
    st.markdown(f'<div class="resumo-box"><b>Resumo IA:</b> {res["Resumo"]}</div>', unsafe_allow_html=True)
    if st.button("Limpar para Novo Registro"):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# --- REGISTRO DE OUVIDORIAS (BOTÃO DE DOWNLOAD) ---
st.markdown('<p class="titulo-custom">📊 Registro de Ouvidorias</p>', unsafe_allow_html=True)
excel_path = os.path.join(os.path.dirname(__file__), "Registro_Ouvidorias_SARO.xlsx")

if os.path.exists(excel_path):
    with open(excel_path, "rb") as f:
        st.markdown('<div class="area-link">', unsafe_allow_html=True)
        st.write("Clique no link abaixo e acesse o arquivo Excel de registro de ouvidorias:")
        st.download_button(
            label="📂 LINK DO ARQUIVO: REGISTRO_OUVIDORIAS_SARO",
            data=f,
            file_name="Registro_Ouvidorias_SARO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("O arquivo será gerado após o primeiro registro.")
