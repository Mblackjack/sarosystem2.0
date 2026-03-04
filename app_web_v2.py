# -*- coding: utf-8 -*-
import streamlit as st
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

# Estilos Visuais
st.markdown("""
<style>
    .caixa-res { border: 2px solid #960018; padding: 20px; border-radius: 10px; background: #fff; margin-top: 20px; }
    .label-vermelho { color: #960018; font-weight: bold; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; width: 100%; height: 50px; font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

# Inicialização única do motor
@st.cache_resource
def iniciar_motor():
    return ClassificadorDenuncias()

try:
    motor = iniciar_motor()
except:
    st.error("Falha ao iniciar motor. Verifique os arquivos no GitHub.")
    st.stop()

st.title("⚖️ Sistema SARO - MPRJ")
st.markdown("---")

with st.form("main_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    n_com = c1.text_input("Nº Comunicação")
    n_mprj = c2.text_input("Nº MPRJ")
    
    endereco = st.text_input("Endereço do Fato (Rua, Bairro, Município)")
    denuncia = st.text_area("Descrição da Ouvidoria", height=150)
    
    f1, f2 = st.columns(2)
    resp = f1.radio("Responsável", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    venc = f2.radio("Consumidor Venceu?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("🚀 REGISTRAR E CLASSIFICAR"):
        if endereco and denuncia:
            with st.spinner("IA Analisando..."):
                res = motor.processar_denuncia(endereco, denuncia, n_com, n_mprj, venc, resp)
                st.session_state.ultimo = res
        else:
            st.error("Preencha os campos obrigatórios.")

# Exibição do Resultado
if "ultimo" in st.session_state:
    r = st.session_state.ultimo
    st.markdown(f"""
    <div class="caixa-res">
        <h3>✅ Registro Concluído</h3>
        <p><span class="label-vermelho">LOCAL:</span> {r['municipio']} | {r['promotoria']}</p>
        <p><span class="label-vermelho">CLASSIFICAÇÃO:</span> {r['tema']} - {r['subtema']}</p>
        <p><span class="label-vermelho">RESUMO:</span> {r['resumo']}</p>
    </div>
    """, unsafe_allow_html=True)
