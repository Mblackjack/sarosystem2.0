# -*- coding: utf-8 -*-
import json
import requests
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from datetime import datetime

# Força o uso da API estável
os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never"

class ClassificadorDenuncias:
    def __init__(self):
        # 1. BUSCA DE CHAVES
        api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # Mudamos para o Pro que é mais estável para evitar o erro 404 v1beta
                self.model = genai.GenerativeModel('gemini-1.5-pro')
            except Exception as e:
                st.error(f"Erro ao configurar Google AI: {e}")
        else:
            st.error("ERRO: GOOGLE_API_KEY não encontrada no Render (aba Environment).")

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
            st.error(f"Erro crítico ao carregar bases JSON: {e}")

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

        # CLASSIFICAÇÃO IA
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = (f"Analise: {denuncia}. Catálogo: {catalogo}. "
                  "Retorne APENAS um JSON com chaves: tema, subtema, empresa, resumo.")
        
        try:
            res = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Limpeza de segurança caso a IA envie markdown ```json
            limpo = res.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(limpo)
            
        except Exception as e:
            st.warning(f"IA indisponível no momento. Detalhe: {e}")
            dados_ia = {
                "tema": "Outros", 
                "subtema": "Geral", 
                "empresa": "N/D", 
                "resumo": "Processamento manual necessário."
            }

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
            "empresa": str(dados_ia.get("empresa", "N/D")).title(),
            "vencedor": vencedor, 
            "responsavel": responsavel
        }

        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json=dados_final, timeout=10)
            except:
                pass
        
        return dados_final
