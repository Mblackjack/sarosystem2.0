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
            if "GOOGLE_API_KEY" in st.secrets:
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                # CORREÇÃO AQUI: Usando a versão estável e mais recente
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            else:
                st.error("Chave GOOGLE_API_KEY não encontrada nos Secrets.")
        except Exception as e:
            st.error(f"Erro ao configurar IA: {e}")
        
        self.webhook_url = st.secrets.get("GSHEET_WEBHOOK", "")
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            path_temas = os.path.join(self.base_path, "base_temas_subtemas.json")
            path_prom = os.path.join(self.base_path, "base_promotorias.json")
            
            with open(path_temas, 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(path_prom, 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
            
            self.municipio_para_promotoria = {}
            for nucleo, d in self.base_promotorias.items():
                for m in d["municipios"]:
                    self.municipio_para_promotoria[m.upper()] = {
                        "promotoria": d["promotoria"], 
                        "municipio_oficial": m
                    }
        except Exception as e:
            st.error(f"Erro ao ler arquivos JSON: {e}")

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

        # IA Config
        try:
            catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
            prompt = (f"Analise a denúncia: {denuncia}. Use este catálogo: {catalogo}. "
                      "Retorne EXCLUSIVAMENTE um JSON com as chaves: tema, subtema, empresa, resumo.")
            
            res = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Limpeza de segurança na resposta
            texto_ia = res.text.strip()
            dados_ia = json.loads(texto_ia)
            
        except Exception as e:
            st.error(f"Erro na IA (Verifique a API Key): {e}")
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "N/D", "resumo": "Processamento manual."}

        # Montagem dos dados
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

        # Envio para Planilha
        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json=dados_final, timeout=10)
            except:
                pass
        
        return dados_final
