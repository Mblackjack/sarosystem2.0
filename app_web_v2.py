# -*- coding: utf-8 -*-
import json
import requests
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from datetime import datetime

class ClassificadorDenuncias:
    def __init__(self):
        try:
            # Puxa a chave dos Secrets
            api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=api_key)
            # Usando a versão mais estável do flash
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"Erro na Chave da IA: {e}")
        
        self.webhook_url = st.secrets.get("GSHEET_WEBHOOK")
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
            
            self.municipio_para_promotoria = {}
            for nucleo, d in self.base_promotorias.items():
                for m in d["municipios"]:
                    self.municipio_para_promotoria[m.upper()] = {
                        "promotoria": d["promotoria"], 
                        "municipio_oficial": m
                    }
        except Exception as e:
            st.error(f"Erro bases JSON: {e}")

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # 1. Identificar Município
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. IA - Prompt Rígido para evitar erro C
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = (f"Analise: {denuncia}. Use este catálogo: {catalogo}. "
                  "Responda APENAS um objeto JSON com: tema, subtema, empresa, resumo (máx 10 palavras).")
        
        try:
            # Força o Gemini a responder JSON puro
            res = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            dados_ia = json.loads(res.text)
        except Exception as e:
            # Fallback caso a IA falhe
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "Não identificada", "resumo": "Processamento manual."}

        # 3. Formatação dos Dados
        dados_final = {
            "num_com": str(num_com),
            "num_mprj": str(num_mprj),
            "promotoria": promotoria,
            "municipio": municipio_nome,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "denuncia": denuncia,
            "resumo": dados_ia.get("resumo", "Sem resumo"),
            "tema": dados_ia.get("tema", "Outros"),
            "subtema": dados_ia.get("subtema", "Geral"),
            "empresa": str(dados_ia.get("empresa", "N/D")).title(),
            "vencedor": vencedor,
            "responsavel": responsavel
        }

        # 4. Envio para Planilha (Webhook)
        if self.webhook_url:
            try:
                # Timeout curto para não travar o usuário
                requests.post(self.webhook_url, json=dados_final, timeout=10)
            except:
                st.warning("IA funcionou, mas a planilha está lenta. O registro será processado em breve.")
        
        return dados_final
