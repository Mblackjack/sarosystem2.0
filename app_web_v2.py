# -*- coding: utf-8 -*-
import streamlit as st
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

# Estilo MPRJ
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .titulo-custom { color: #960018; font-weight: bold; font-size: 1.5rem; }
    .area-link { border: 2px dashed #960018; padding: 25px; text-align: center; border-radius: 10px; background-color: #fffafa; margin-top: 20px; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

# Inicialização
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao iniciar sistema: {e}")
    st.stop()

# Sidebar
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.sidebar.divider()
st.sidebar.info("SARO v2.0 - Versão Integrada ao Google Drive")

st.title("⚖️ Sistema SARO - MPRJ")
st.markdown("---")

# --- TÓPICO 1: NOVO REGISTRO DE OUVIDORIA ---
with st.form("form_registro", clear_on_submit=True):
    st.markdown('<p class="titulo-custom">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        num_com = st.text_input("Nº de Comunicação", placeholder="Ex: 123/2024")
    with col2:
        num_mprj = st.text_input("Nº MPRJ", placeholder="Ex: 2024.001.002")
        
    endereco = st.text_input("Endereço da Denúncia", placeholder="Rua, Bairro, Município - RJ")
    denuncia = st.text_area("Descrição da Ouvidoria", placeholder="Cole aqui o texto da denúncia...")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        responsavel = st.radio("Enviado por:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with col_f2:
        vencedor = st.radio("O consumidor é vencedor?", ["Sim", "Não"], horizontal=True)
        
    submit = st.form_submit_button("REGISTRAR OUVIDORIA", use_container_width=True)

if submit:
    if not endereco or not denuncia:
        st.error("❌ Por favor, preencha o Endereço e a Descrição!")
    else:
        with st.spinner("IA processando e sincronizando com a planilha..."):
            try:
                # Processa e salva na planilha online automaticamente
                res = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.session_state.resultado = res
                st.success("✅ Registro realizado com sucesso na Planilha Google!")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

# --- TÓPICO 2: REGISTRO DA CLASSIFICAÇÃO ATUAL ---
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown('<p class="titulo-custom">✅ Registro da Classificação Atual</p>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Empresa/Órgão", res.get('Empresa'))
    c2.metric("Tema", res.get('Tema'))
    c3.metric("Município", res.get('Município'))
    
    st.markdown(f"🏛️ **Promotoria Responsável:** {res.get('Promotoria')}")
    st.markdown(f"📧 **Subtema:** {res.get('Subtema')}")
    
    st.markdown("**Resumo da IA (Máximo 10 palavras):**")
    st.markdown(f'<div class="resumo-box">{res.get("Resumo")}</div>', unsafe_allow_html=True)
    
    if st.button("➕ Limpar e Nova Ouvidoria", use_container_width=True):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# --- TÓPICO 3: REGISTRO DE OUVIDORIAS (ÁREA DO LINK) ---
st.markdown('<p class="titulo-custom">📊 Registro de Ouvidorias</p>', unsafe_allow_html=True)
link_planilha = st.secrets.get("GSHEET_URL")

st.markdown(f"""
<div class="area-link">
    <p style="font-size: 1.1rem; color: #333;">Clique no link abaixo para acessar o arquivo Excel de registro de ouvidorias:</p>
    <a href="{link_planilha}" target="_blank" style="text-decoration: none;">
        <span style="font-size: 1.3rem; color: #960018; font-weight: bold; border-bottom: 2px solid #960018;">
            📂 LINK DO ARQUIVO: REGISTRO_OUVIDORIAS_SARO
        </span>
    </a>
    <p style="margin-top: 15px; font-size: 0.9rem; color: #666;">(Acesso restrito aos usuários autorizados do MPRJ)</p>
</div>
""", unsafe_allow_html=True)

st.caption("SARO v2.0 - Criado por Matheus Pereira Barreto")
