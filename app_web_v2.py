# -*- coding: utf-8 -*-
import streamlit as st
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

# Estilo CSS para replicar o visual da versão anterior
st.markdown("""
<style>
    .caixa-resultado {
        border: 1px solid #960018;
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        margin-bottom: 20px;
    }
    .label-vermelho { color: #960018; font-weight: bold; }
    .titulo-custom { color: #960018; font-weight: bold; font-size: 1.5rem; }
    .badge-verde {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
        margin-right: 10px;
        border: 1px solid #c8e6c9;
    }
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .area-planilha { border: 2px solid #960018; padding: 25px; text-align: center; border-radius: 10px; background-color: #ffffff; margin-top: 20px; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao iniciar sistema: {e}")
    st.stop()

st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.title("⚖️ Sistema Automático de Registro de Ouvidorias (SARO)")
st.markdown("*Versão 2.0* | Registro e Gestão de Ouvidorias com auxílio de Inteligência Artificial")
st.divider()

# --- FORMULÁRIO DE REGISTRO ---
with st.form("form_reg", clear_on_submit=True):
    st.markdown('<p class="titulo-custom">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    num_com = col1.text_input("Nº de Comunicação")
    num_mprj = col2.text_input("Nº MPRJ")
    
    endereco = st.text_input("Endereço Completo")
    denuncia = st.text_area("Descrição da Ouvidoria", height=150)
    
    f1, f2 = st.columns(2)
    responsavel = f1.radio("Responsável:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = f2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("🔍Registrar Ouvidoria", use_container_width=True):
        if endereco and denuncia:
            with st.spinner("Processando..."):
                res = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.session_state.resultado = res
                st.success("✅ Enviado para o Arquivo de Ouvidorias!")
        else:
            st.error("Preencha Endereço e Descrição.")

# --- TÓPICO: REGISTRO DA CLASSIFICAÇÃO ATUAL (VERSÃO ANTERIOR) ---
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown("### ✅ Resultado da Classificação Atual")
    
    # Box com informações principais
    st.markdown(f"""
    <div class="caixa-resultado">
        <div style="display: flex; justify-content: space-between;">
            <p><span class="label-vermelho">Nº Comunicação:</span> {res['num_com']}</p>
            <p><span class="label-vermelho">Nº MPRJ:</span> {res['num_mprj']}</p>
        </div>
        <p>📍 <span class="label-vermelho">Município:</span> {res['municipio']}</p>
        <p>🏛️ <span class="label-vermelho">Promotoria Responsável:</span> {res['promotoria']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Badges de Tema, Subtema e Empresa
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.markdown(f'<div class="badge-verde">Tema: {res["tema"]}</div>', unsafe_allow_html=True)
    col_t2.markdown(f'<div class="badge-verde">Subtema: {res["subtema"]}</div>', unsafe_allow_html=True)
    col_t3.markdown(f'<div class="badge-verde">Empresa: {res["empresa"]}</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Resumo da IA (Máximo 10 palavras):**")
    st.markdown(f'<div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)
    
    # Expander com a descrição original
    with st.expander("📄 Ver Descrição da Ouvidoria"):
        st.write(res['denuncia'])
    
    if st.button("Limpar Tela para Novo Registro"):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# --- TÓPICO: REGISTRO DE OUVIDORIAS (LINK) ---
st.markdown('<p class="titulo-custom">📊 Registro de Ouvidorias</p>', unsafe_allow_html=True)
url_planilha = "https://docs.google.com/spreadsheets/d/1RqvTGIawKh9Kdj8e-9BFPpi33xkNeA33ItKAaUC40xc/edit"

st.markdown(f"""
<div class="area-planilha">
    <p>Acesse a planilha oficial atualizada em tempo real:</p>
    <a href="{url_planilha}" target="_blank" style="font-weight: bold; color: #960018; font-size: 1.2rem;">
        📂 Abrir Planilha de Ouvidorias
    </a>
</div>
""", unsafe_allow_html=True)

st.divider()

st.caption("SARO v2.0 - Sistema Automático de Registro de Ouvidorias | Ministério Público do Rio de Janeiro (Created by Matheus Pereira Barreto [62006659])")
