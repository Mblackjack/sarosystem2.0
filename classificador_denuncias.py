# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração da API do Gemini via Secrets
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("Chave API do Google não encontrada nos Secrets!")
            st.stop()
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 2. Caminhos e Bases de Dados Locais (JSONs)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()
        
        # 3. Inicialização da Conexão com Google Sheets
        self.conn = st.connection("gsheets", type=GSheetsConnection)

    def carregar_bases(self):
        """Carrega os arquivos JSON de temas e promotorias"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
            
            # Mapeamento rápido de município para promotoria
            self.municipio_para_promotoria = {
                m.upper(): {"promotoria": d["promotoria"], "municipio_oficial": m}
                for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
            }
        except Exception as e:
            st.error(f"Erro ao carregar arquivos JSON: {e}")

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def salvar_na_planilha_online(self, dados: dict):
        """Lê a planilha atual e adiciona a nova linha no Google Drive"""
        try:
            url = st.secrets.get("GSHEET_URL")
            # Lê os dados que já existem na planilha
            df_existente = self.conn.read(spreadsheet=url)
            
            # Cria um DataFrame com a nova linha
            df_novo_registro = pd.DataFrame([dados])
            
            # Junta o antigo com o novo
            df_final = pd.concat([df_existente, df_novo_registro], ignore_index=True)
            
            # Faz o upload (Update) para o Google Sheets
            self.conn.update(spreadsheet=url, data=df_final)
            return True
        except Exception as e:
            st.error(f"Erro ao sincronizar com o Google Sheets: {e}")
            return False

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        """Processa a inteligência artificial e identifica a promotoria"""
        
        # --- Identificação Geográfica ---
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # --- Classificação por IA (Gemini) ---
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = (
            f"Analise a denúncia: {denuncia}. "
            f"Utilize estritamente este catálogo para tema e subtema: {catalogo}. "
            "Retorne APENAS um JSON com as chaves: tema, subtema, empresa, resumo. "
            "O resumo deve ter no máximo 10 palavras."
        )
        
        try:
            response = self.model.generate_content(prompt)
            # Limpa possíveis blocos de código markdown da resposta
            txt_limpo = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(txt_limpo)
        except:
            dados_ia = {
                "tema": "Outros", 
                "subtema": "Geral", 
                "empresa": "Não identificada", 
                "resumo": "Erro no processamento automático da IA."
            }

        # --- Montagem do Registro Final ---
        registro_final = {
            "Nº Comunicação": num_com,
            "Nº MPRJ": num_mprj,
            "Promotoria": promotoria,
            "Município": municipio_nome,
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Denúncia": denuncia,
            "Resumo": dados_ia.get("resumo", ""),
            "Tema": dados_ia.get("tema", "Outros"),
            "Subtema": dados_ia.get("subtema", "Geral"),
            "Empresa": str(dados_ia.get("empresa", "Não identificada")).strip().title(),
            "É Consumidor Vencedor?": vencedor,
            "Enviado por:": responsavel
        }
        
        # --- Salvar no Google Sheets ---
        self.salvar_na_planilha_online(registro_final)
        
        return registro_final
