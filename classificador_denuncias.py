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
        # 1. BUSCA DE CHAVES (Compatível com Render e Streamlit)
        # O os.environ busca nas variáveis que você cadastrou no painel do Render
        api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        self.webhook_url = os.environ.get("GSHEET_WEBHOOK") or st.secrets.get("GSHEET_WEBHOOK")

        if not api_key:
            st.error("ERRO: GOOGLE_API_KEY não configurada no painel Environment do Render.")
            return

        try:
            genai.configure(api_key=api_key)
            # Usando nome estável para evitar erro 404/v1beta
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        except Exception as e:
            st.error(f"Erro ao configurar o modelo Gemini: {e}")

        # 2. BASES LOCAIS
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            path_temas = os.path.join(self.base_path, "base_temas_subtemas.json")
            path_promotorias = os.path.join(self.base_path, "base_promotorias.json")
            
            with open(path_temas, 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(path_promotorias, 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)

            self.municipio_para_promotoria = {}
            for nucleo, d in self.base_promotorias.items():
                for m in d["municipios"]:
                    self.municipio_para_promotoria[m.upper()] = {
                        "promotoria": d["promotoria"], 
                        "municipio_oficial": m
                    }
        except Exception as e:
            st.error(f"Erro ao carregar arquivos JSON: {e}")

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # 1. IDENTIFICAR MUNICÍPIO/PROMOTORIA
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(str(endereco).upper())
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. CLASSIFICAÇÃO IA COM GARANTIA DE JSON
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = (f"Analise a denúncia: {denuncia}. Use este catálogo: {catalogo}. "
                  "Retorne EXCLUSIVAMENTE um JSON com chaves: tema, subtema, empresa, resumo.")
        
        try:
            # Forçamos o modelo a responder em formato JSON puro
            res = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            dados_ia = json.loads(res.text)
        except Exception as e:
            st.warning(f"IA falhou, usando classificação padrão. Erro: {e}")
            dados_ia = {
                "tema": "Outros", 
                "subtema": "Geral", 
                "empresa": "Não identificada", 
                "resumo": "Processamento manual necessário."
            }

        # 3. MONTAR DADOS FINAIS
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

        # 4. ENVIO PARA O GOOGLE SHEETS (WEBHOOK)
        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json=dados_final, timeout=10)
            except Exception as e:
                st.error(f"IA funcionou, mas falhou ao enviar para a planilha: {e}")
        
        return dados_final
