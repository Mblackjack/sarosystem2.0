# -*- coding: utf-8 -*-
import streamlit as st
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

# Estilo Institucional MPRJ
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .titulo-custom { color: #960018; font-weight: bold; font-size: 1.5rem; }
    .area-planilha { border: 2px solid #960018; padding: 25px; text-align: center; border-radius: 10px; background-color: #ffffff; margin-top: 20px; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Inicialização da lógica
if "resultado" not in st.session_state:
    st.session_state.resultado = None

# Tenta carregar o classificador
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao iniciar sistema. Verifique os Secrets. Detalhe: {e}")
    st.stop()

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.sidebar.divider()
st.sidebar.info("SARO v2.0 - Sistema de Ouvidorias")
st.sidebar.caption("Integrado com Planilha Viva")

# --- TÍTULO PRINCIPAL ---
st.title("⚖️ Sistema SARO - MPRJ")
st.divider()

# --- TÓPICO 1: NOVO REGISTRO DE OUVIDORIA ---
with st.form("form_reg", clear_on_submit=True):
    st.markdown('<p class="titulo-custom">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        num_com = st.text_input("Nº de Comunicação", placeholder="Ex: 001/2025")
    with c2:
        num_mprj = st.text_input("Nº MPRJ", placeholder="Ex: 2025.0001.0002")
        
    endereco = st.text_input("Endereço Completo (Município é essencial para identificar a Promotoria)")
    denuncia = st.text_area("Descrição da Ouvidoria", height=150)
    
    f1, f2 = st.columns(2)
    with f1:
        responsavel = st.radio("Responsável pelo Registro:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with f2:
        vencedor = st.radio("O consumidor é vencedor?", ["Sim", "Não"], horizontal=True)
    
    submit_button = st.form_submit_button("REGISTRAR NA PLANILHA VIVA", use_container_width=True)

# Processamento do formulário
if submit_button:
    if endereco and denuncia:
        with st.spinner("Classificando via IA e sincronizando com a planilha..."):
            # Envia os dados para o classificador que agora usa o Webhook (URL /exec)
            res = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
            st.session_state.resultado = res
            st.success("✅ Sucesso! O registro foi enviado para a Planilha Viva.")
    else:
        st.error("Por favor, preencha os campos obrigatórios (Endereço e Denúncia).")

# --- TÓPICO 2: REGISTRO DA CLASSIFICAÇÃO ATUAL ---
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown('<p class="titulo-custom">✅ Registro da Classificação Atual</p>', unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Empresa/Órgão", res["empresa"])
    col_b.metric("Tema", res["tema"])
    col_c.metric("Município", res["municipio"])
    
    st.write(f"**🏛️ Promotoria Responsável:** {res['promotoria']}")
    st.markdown(f"**Resumo da IA (Máximo 10 palavras):**")
    st.markdown(f'<div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)
    
    if st.button("➕ Novo Registro"):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# --- TÓPICO 3: REGISTRO DE OUVIDORIAS (ÁREA DO LINK) ---
st.markdown('<p class="titulo-custom">📊 Registro de Ouvidorias</p>', unsafe_allow_html=True)

# URL da sua planilha real
url_planilha = "https://docs.google.com/spreadsheets/d/1RqvTGIawKh9Kdj8e-9BFPpi33xkNeA33ItKAaUC40xc/edit"

st.markdown(f"""
<div class="area-planilha">
    <p style="font-size: 1.1rem; color: #333;">Acesse a planilha oficial que recebe os dados em tempo real:</p>
    <a href="{url_planilha}" target="_blank" style="text-decoration: none;">
        <span style="font-size: 1.3rem; color: #960018; font-weight: bold; border-bottom: 2px solid #960018;">
            📂 ABRIR PLANILHA DE REGISTROS (GOOGLE DRIVE)
        </span>
    </a>
    <p style="margin-top: 15px; font-size: 0.9rem; color: #666;">(As atualizações aparecem instantaneamente após cada registro)</p>
</div>
""", unsafe_allow_html=True)

st.caption("SARO v2.0 | Desenvolvido para o MPRJ")
