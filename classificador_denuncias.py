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
        api_key = st.secrets.get("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()
        # Conexão direta com Google Sheets
        self.conn = st.connection("gsheets", type=GSheetsConnection)

    def carregar_bases(self):
        with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
            self.temas_subtemas = json.load(f)
        with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
            self.base_promotorias = json.load(f)
        
        self.municipio_para_promotoria = {
            m.upper(): {"promotoria": d["promotoria"], "municipio_oficial": m}
            for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
        }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def salvar_online(self, dados: dict):
        """Adiciona os dados diretamente na planilha do link"""
        try:
            url = st.secrets.get("GSHEET_URL")
            # Lê a planilha atual
            df_atual = self.conn.read(spreadsheet=url)
            # Cria a nova linha
            nova_linha = pd.DataFrame([dados])
            # Concatena e faz o update total
            df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
            self.conn.update(spreadsheet=url, data=df_final)
            return True
        except Exception as e:
            st.error(f"Erro ao sincronizar com o Excel Online: {e}")
            return False

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # Identificação de Local
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # IA
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = f"Classifique: {denuncia}. Use o catálogo: {catalogo}. Retorne JSON: tema, subtema, empresa, resumo (10 palavras)."
        
        try:
            res = self.model.generate_content(prompt)
            txt = res.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(txt)
        except:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "Não identificada", "resumo": "Processado manualmente"}

        resultado = {
            "Nº Comunicação": num_com,
            "Nº MPRJ": num_mprj,
            "Promotoria": promotoria,
            "Município": municipio_nome,
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Denúncia": denuncia,
            "Resumo": dados_ia.get("resumo"),
            "Tema": dados_ia.get("tema"),
            "Subtema": dados_ia.get("subtema"),
            "Empresa": str(dados_ia.get("empresa")).title(),
            "É Consumidor Vencedor?": vencedor,
            "Enviado por:": responsavel
        }
        
        self.salvar_online(resultado)
        return resultado
