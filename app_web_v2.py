# -*- coding: utf-8 -*-
"""
SARO v6.0 - Sistema Automático de Registro de Ouvidorias
Interface Web com Streamlit - Integração Total com Excel em Tempo Real
"""

import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from classificador_denuncias import ClassificadorDenuncias
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="SARO - Sistema de Ouvidorias", layout="wide")

# Caminhos dos arquivos
BASE_DIR = "/home/ubuntu/mprj_denuncias"
HISTORICO_JSON = os.path.join(BASE_DIR, "historico_denuncias.json")
HISTORICO_EXCEL = os.path.join(BASE_DIR, "SARO_Ouvidorias_Registradas.xlsx")

# CSS customizado
st.markdown("""
<style>
    .resumo-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .tabela-container {
        max-height: 700px;
        overflow-y: auto;
        overflow-x: auto;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
    }
    .modal-container {
        background-color: #f9f9f9;
        border: 2px solid #1f77b4;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }
    .excel-link {
        background-color: #217346;
        color: white !important;
        padding: 10px 20px;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Funções de Persistência
def salvar_dados(historico):
    # Salvar JSON (Backup)
    with open(HISTORICO_JSON, 'w', encoding='utf-8') as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)
    
    # Salvar Excel (Principal)
    if historico:
        df = pd.DataFrame(historico)
        # Reordenar colunas para o Excel ficar organizado
        colunas_ordem = [
            "data", "num_comunicacao", "num_mprj", "responsavel", "consumidor_vencedor",
            "municipio", "promotoria", "tema", "subtema", "empresa", "resumo", "endereco", "denuncia"
        ]
        # Garantir que todas as colunas existam
        for col in colunas_ordem:
            if col not in df.columns:
                df[col] = ""
        
        df = df[colunas_ordem]
        df.columns = [
            "Data", "Nº Comunicação", "Nº MPRJ", "Responsável", "Consumidor Vencedor",
            "Município", "Promotoria", "Tema", "Subtema", "Empresa", "Resumo", "Endereço", "Descrição Completa"
        ]
        df.to_excel(HISTORICO_EXCEL, index=False)

def carregar_dados():
    if os.path.exists(HISTORICO_JSON):
        with open(HISTORICO_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Inicializar estado da sessão
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "historico" not in st.session_state:
    st.session_state.historico = carregar_dados()
if "visualizando_registro" not in st.session_state:
    st.session_state.visualizando_registro = None

# Cabeçalho
st.title("⚖️ SARO - Sistema Automático de Registro de Ouvidorias")
st.markdown("**Versão 6.0** | Integração em Tempo Real com Excel")

# Link para o Excel na Barra Lateral
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Microsoft_Office_Excel_%282019%E2%80%93present%29.svg/1200px-Microsoft_Office_Excel_%282019%E2%80%93present%29.svg.png", width=50)
    st.markdown("### 📁 Banco de Dados Excel")
    
    if os.path.exists(HISTORICO_EXCEL):
        with open(HISTORICO_EXCEL, "rb") as file:
            st.download_button(
                label="📥 Baixar Planilha de Ouvidorias",
                data=file,
                file_name="SARO_Ouvidorias_Registradas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.info("A planilha será gerada após o primeiro registro.")
    
    st.divider()
    st.caption("O arquivo Excel é atualizado automaticamente a cada novo registro.")

st.divider()

# Inicializar classificador
classificador = ClassificadorDenuncias()

# ============ VISUALIZAÇÃO DE REGISTRO ============
if st.session_state.visualizando_registro is not None:
    registro = st.session_state.visualizando_registro
    st.markdown("### 📋 Detalhes da Ouvidoria")
    with st.container():
        st.markdown('<div class="modal-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f"**Nº Comunicação:** {registro.get('num_comunicacao', 'N/A')}")
        with col2: st.markdown(f"**Nº MPRJ:** {registro.get('num_mprj', 'N/A')}")
        with col3: st.markdown(f"**Data:** {registro.get('data', 'N/A')}")
        col1, col2 = st.columns(2)
        with col1: st.markdown(f"**Responsável:** {registro.get('responsavel', 'N/A')}")
        with col2: st.markdown(f"**Consumidor Vencedor:** {registro.get('consumidor_vencedor', 'N/A')}")
        st.markdown(f"**Endereço:** {registro.get('endereco', 'N/A')}")
        st.markdown(f"**Município:** {registro.get('municipio', 'N/A')} | **Promotoria:** {registro.get('promotoria', 'N/A')}")
        st.markdown(f"**Tema:** {registro.get('tema', 'N/A')} | **Subtema:** {registro.get('subtema', 'N/A')} | **Empresa:** {registro.get('empresa', 'N/A')}")
        st.markdown("**Resumo:**")
        st.info(registro.get('resumo', 'N/A'))
        with st.expander("Ver Descrição Completa"):
            st.write(registro.get('denuncia', 'N/A'))
        if st.button("❌ Fechar Visualização"):
            st.session_state.visualizando_registro = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

# ============ FORMULÁRIO DE OUVIDORIA ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown("### 📝 Novo Registro")
    col1, col2 = st.columns(2)
    with col1: num_comunicacao = st.text_input("Nº de Comunicação")
    with col2: num_mprj = st.text_input("Nº MPRJ")
    endereco = st.text_input("Endereço da Denúncia")
    denuncia = st.text_area("Descrição da Ouvidoria")
    col1, col2 = st.columns(2)
    with col1:
        responsavel = st.radio("Enviado por:", options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with col2:
        consumidor_vencedor = st.radio("É consumidor vencedor?", options=["Sim", "Não"], horizontal=True)
    submit = st.form_submit_button("🔍 Processar e Salvar no Excel", use_container_width=True, type="primary")

if submit:
    if not endereco or not denuncia:
        st.error("❌ Preencha o Endereço e a Descrição!")
    else:
        with st.spinner("Processando e salvando..."):
            resultado = classificador.processar_denuncia(endereco, denuncia, num_comunicacao, num_mprj)
            resultado.update({
                "responsavel": responsavel,
                "consumidor_vencedor": consumidor_vencedor,
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            })
            st.session_state.resultado = resultado
            st.session_state.historico.append(resultado)
            salvar_dados(st.session_state.historico)
            st.success("✅ Registrado com sucesso no Excel!")
            st.rerun()

# ============ REGISTRO DE OUVIDORIAS (HISTÓRICO) ============
st.divider()
st.markdown("### 📊 Histórico de Registros")

if not st.session_state.historico:
    st.info("Nenhum registro encontrado.")
else:
    col1, col2 = st.columns([3, 1])
    with col1: search = st.text_input("🔍 Buscar", placeholder="Pesquise...")
    with col2: filtro_tema = st.selectbox("Tema", ["Todos"] + sorted(list(set(h['tema'] for h in st.session_state.historico))))

    dados_filtrados = st.session_state.historico
    if search:
        search = search.lower()
        dados_filtrados = [h for h in dados_filtrados if any(search in str(v).lower() for v in h.values())]
    if filtro_tema != "Todos":
        dados_filtrados = [h for h in dados_filtrados if h['tema'] == filtro_tema]

    st.markdown('<div class="tabela-container">', unsafe_allow_html=True)
    cols = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1.5, 1, 1])
    headers = ["Nº Com.", "Nº MPRJ", "Data", "Promotoria", "Município", "Responsável", "Ver", "Del"]
    for col, header in zip(cols, headers): col.write(f"**{header}**")
    st.divider()
    
    for registro in reversed(dados_filtrados):
        idx_original = st.session_state.historico.index(registro)
        cols = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1.5, 1, 1])
        cols[0].write(registro.get('num_comunicacao', 'N/A'))
        cols[1].write(registro.get('num_mprj', 'N/A'))
        cols[2].write(registro.get('data', 'N/A'))
        cols[3].write(registro.get('promotoria', 'N/A'))
        cols[4].write(registro.get('municipio', 'N/A'))
        cols[5].write(registro.get('responsavel', 'N/A'))
        if cols[6].button("👁️", key=f"v_{idx_original}"):
            st.session_state.visualizando_registro = registro
            st.rerun()
        if cols[7].button("🗑️", key=f"d_{idx_original}"):
            st.session_state.historico.pop(idx_original)
            salvar_dados(st.session_state.historico)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("SARO v6.0 | Banco de Dados Excel Sincronizado")
