# -*- coding: utf-8 -*-
import streamlit as st
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

# CSS para o visual do MPRJ
st.markdown("""
<style>
    .caixa-resultado { border: 1px solid #960018; padding: 20px; border-radius: 10px; background-color: #ffffff; margin-bottom: 20px; }
    .label-vermelho { color: #960018; font-weight: bold; }
    .titulo-custom { color: #960018; font-weight: bold; font-size: 1.5rem; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; width: 100%; }
</style>
""", unsafe_allow_html=True)

# Inicia o motor do sistema
if "classificador" not in st.session_state:
    try:
        st.session_state.classificador = ClassificadorDenuncias()
    except Exception as e:
        st.error(f"Erro ao carregar o motor do sistema: {e}")

st.title("⚖️ Sistema SARO - MPRJ")
st.markdown("*Versão 2.0* | Inteligência Artificial")

# Formulário
with st.form("registro", clear_on_submit=True):
    col1, col2 = st.columns(2)
    n_com = col1.text_input("Nº Comunicação")
    n_mprj = col2.text_input("Nº MPRJ")
    end = st.text_input("Endereço Completo")
    den = st.text_area("Descrição da Denúncia", height=150)
    
    f1, f2 = st.columns(2)
    resp = f1.radio("Responsável", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    venc = f2.radio("Vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("🔍 REGISTRAR AGORA"):
        if end and den:
            with st.spinner("IA Processando..."):
                resultado = st.session_state.classificador.processar_denuncia(end, den, n_com, n_mprj, venc, resp)
                st.session_state.ultimo_res = resultado
                st.success("✅ Registrado com sucesso!")
        else:
            st.error("Preencha Endereço e Denúncia.")

# Exibe o resultado se existir
if "ultimo_res" in st.session_state:
    res = st.session_state.ultimo_res
    st.markdown(f"""
    <div class="caixa-resultado">
        <p><span class="label-vermelho">MUNICÍPIO:</span> {res['municipio']}</p>
        <p><span class="label-vermelho">TEMA:</span> {res['tema']} | <span class="label-vermelho">SUBTEMA:</span> {res['subtema']}</p>
        <p><span class="label-vermelho">RESUMO:</span> {res['resumo']}</p>
    </div>
    """, unsafe_allow_html=True)
