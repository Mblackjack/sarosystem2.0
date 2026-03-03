# -*- coding: utf-8 -*-
import streamlit as st
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    .caixa-resultado { border: 1px solid #960018; padding: 20px; border-radius: 10px; background-color: #ffffff; margin-bottom: 20px; }
    .label-vermelho { color: #960018; font-weight: bold; }
    .titulo-custom { color: #960018; font-weight: bold; font-size: 1.5rem; }
    .badge-verde { background-color: #e8f5e9; color: #2e7d32; padding: 10px 20px; border-radius: 8px; font-weight: bold; display: inline-block; margin-right: 10px; border: 1px solid #c8e6c9; }
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro Crítico: {e}")
    st.stop()

st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.title("⚖️ SARO 2.0")
st.markdown("Sistema Automático de Registro de Ouvidorias")
st.divider()

with st.form("form_reg", clear_on_submit=True):
    st.markdown('<p class="titulo-custom">📝 Novo Registro</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    n_com = c1.text_input("Nº de Comunicação")
    n_mprj = c2.text_input("Nº MPRJ")
    end = st.text_input("Endereço Completo")
    desc = st.text_area("Descrição da Ouvidoria")
    
    f1, f2 = st.columns(2)
    resp = f1.radio("Responsável:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    venc = f2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("🔍 Registrar e Classificar", use_container_width=True):
        if end and desc:
            with st.spinner("IA Analisando..."):
                # Captura os dois valores do return
                dados, ok = classificador.processar_denuncia(end, desc, n_com, n_mprj, venc, resp)
                st.session_state.resultado = dados
                if ok: st.success("Registrado com sucesso!")
        else:
            st.error("Preencha os campos obrigatórios.")

if st.session_state.resultado:
    r = st.session_state.resultado
    st.divider()
    st.markdown("### ✅ Resultado da Classificação Atual")
    
    st.markdown(f"""
    <div class="caixa-resultado">
        <p><span class="label-vermelho">Nº Com:</span> {r.get('num_com')} | <span class="label-vermelho">Nº MPRJ:</span> {r.get('num_mprj')}</p>
        <p>📍 <b>Município:</b> {r.get('municipio')} | 🏛️ <b>Promotoria:</b> {r.get('promotoria')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="badge-verde">Tema: {r.get('tema')}</div>
        <div class="badge-verde">Subtema: {r.get('subtema')}</div>
        <div class="badge-verde">Empresa: {r.get('empresa')}</div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><b>Resumo da IA (Com Localização):</b>", unsafe_allow_html=True)
    st.markdown(f'<div class="resumo-box">{r.get("resumo")}</div>', unsafe_allow_html=True)
    
    if st.button("Limpar"):
        st.session_state.resultado = None
        st.rerun()
