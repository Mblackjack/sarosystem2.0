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
        # IA Config - Buscando dos Secrets de forma segura
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        except Exception as e:
            st.error(f"Erro ao configurar chave da IA: {e}")
        
        # URL da Planilha Viva (Webhook para o Google Apps Script)
        self.webhook_url = st.secrets.get("GSHEET_WEBHOOK")
        
        # Bases locais com caminho absoluto para evitar erro 404
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
            st.error(f"Erro ao carregar bases JSON: {e}")

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # 1. Identificar Município/Promotoria
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. Classificação IA - Refinado para ser mais robusto
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = (f"Analise esta denúncia: {denuncia}. Use este catálogo: {catalogo}. "
                  "Responda EXCLUSIVAMENTE um JSON com as chaves: tema, subtema, empresa, resumo (máx 10 palavras).")
        
        try:
            # Uso do generation_config para garantir resposta em JSON
            res = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            dados_ia = json.loads(res.text)
        except:
            dados_ia = {
                "tema": "Outros", 
                "subtema": "Geral", 
                "empresa": "Não identificada", 
                "resumo": "Processamento manual necessário."
            }

        # 3. Montar dados final
        dados_final = {
            "num_com": str(num_com),
            "num_mprj": str(num_mprj),
            "promotoria": promotoria,
            "municipio": municipio_nome,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "denuncia": denuncia,
            "resumo": dados_ia.get("resumo"),
            "tema": dados_ia.get("tema"),
            "subtema": dados_ia.get("subtema"),
            "empresa": str(dados_ia.get("empresa")).title(),
            "vencedor": vencedor,
            "responsavel": responsavel
        }

        # 4. ENVIO PARA A PLANILHA VIVA (Google Apps Script)
        if self.webhook_url:
            try:
                # O Google Script às vezes demora, aumentamos o timeout para 15s
                requests.post(self.webhook_url, json=dados_final, timeout=15)
            except Exception as e:
                st.warning(f"Atenção: A IA classificou, mas a planilha não respondeu a tempo. Erro: {e}")
        
        return dados_final
