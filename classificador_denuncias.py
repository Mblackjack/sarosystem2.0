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
        # BUSCA DE CHAVES: Prioriza o Render (os.environ), depois tenta Streamlit
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            try:
                api_key = st.secrets["GOOGLE_API_KEY"]
            except:
                api_key = None

        if api_key:
            genai.configure(api_key=api_key)
            # MUDANÇA PARA O MODELO PRO: Mais estável contra erros de versão v1beta
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            st.error("ERRO: Chave GOOGLE_API_KEY não configurada no Render.")

        self.webhook_url = os.environ.get("GSHEET_WEBHOOK") or st.secrets.get("GSHEET_WEBHOOK", "")
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
            st.error(f"Erro nos arquivos JSON: {e}")

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(str(endereco).upper())
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        try:
            catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
            prompt = (f"Analise: {denuncia}. Catálogo: {catalogo}. "
                      "Retorne APENAS um JSON com chaves: tema, subtema, empresa, resumo.")
            
            # Forçamos a resposta em JSON estável
            res = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            dados_ia = json.loads(res.text)
        except Exception as e:
            st.error(f"Falha na IA: {e}")
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "N/D", "resumo": "Processamento manual."}

        dados_final = {
            "num_com": str(num_com), "num_mprj": str(num_mprj),
            "promotoria": promotoria, "municipio": municipio_nome,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "denuncia": denuncia, "resumo": dados_ia.get("resumo"),
            "tema": dados_ia.get("tema"), "subtema": dados_ia.get("subtema"),
            "empresa": str(dados_ia.get("empresa")).title(),
            "vencedor": vencedor, "responsavel": responsavel
        }

        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json=dados_final, timeout=10)
            except:
                pass
        
        return dados_final
