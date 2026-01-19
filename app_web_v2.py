# -*- coding: utf-8 -*-
import streamlit as st
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - Entrada de Dados", layout="wide")

# Estilo Institucional
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

# Inicialização
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error("Erro ao iniciar sistema. Verifique os Secrets.")
    st.stop()

# Sidebar
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.sidebar.divider()
if st.secrets.get("GSHEET_URL"):
    st.sidebar.markdown(f"### [📊 Acessar Planilha Oficial]({st.secrets.get('GSHEET_URL')})")

st.title("⚖️ Sistema SARO - MPRJ")

with st.form("form_ouvidoria", clear_on_submit=True):
    st.subheader("📝 Novo Registro")
    c1, c2 = st.columns(2)
    num_com = c1.text_input("Nº de Comunicação")
    num_mprj = c2.text_input("Nº MPRJ")
    
    endereco = st.text_input("Endereço Completo")
    denuncia = st.text_area("Texto da Ouvidoria")
    
    f1, f2 = st.columns(2)
    responsavel = f1.radio("Responsável:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = f2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("REGISTRAR NO EXCEL ONLINE", use_container_width=True):
        if endereco and denuncia:
            with st.spinner("Classificando e salvando na planilha..."):
                res = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.session_state.resultado = res
                st.success("✅ Registro enviado com sucesso!")
        else:
            st.error("Campos obrigatórios: Endereço e Denúncia.")

# MOSTRA APENAS O ÚLTIMO RESULTADO PARA CONFERÊNCIA
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown("### 🔍 Conferência do Registro")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Empresa", res["Empresa"])
    col_b.metric("Tema", res["Tema"])
    col_c.metric("Município", res["Município"])
    
    st.write(f"**🏛️ Destino:** {res['Promotoria']}")
    st.markdown(f"**Resumo da IA:**")
    st.markdown(f'<div class="resumo-box">{res["Resumo"]}</div>', unsafe_allow_html=True)
    
    if st.button("Novo Registro"):
        st.session_state.resultado = None
        st.rerun()

st.caption("SARO v2.0 | Dados integrados via Google Sheets")
