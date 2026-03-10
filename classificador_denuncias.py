# -*- coding: utf-8 -*-
import json
import requests
import os
import unicodedata
import streamlit as st
from mistralai import Mistral
from datetime import datetime

class ClassificadorDenuncias:
    def __init__(self):
        # 1. BUSCA DA KEY (Render Environment)
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            api_key = st.secrets.get("MISTRAL_API_KEY", "")

        if api_key:
            self.client = Mistral(api_key=api_key)
            self.model = "mistral-small-latest" 
        else:
            st.error("ERRO: MISTRAL_API_KEY não configurada no Render.")

        self.webhook_url = os.environ.get("GSHEET_WEBHOOK") or st.secrets.get("GSHEET_WEBHOOK", "")
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
            
            self.municipio_para_promotoria = {
                m.upper(): {"promotoria": d["promotoria"], "municipio_oficial": m}
                for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
            }
        except Exception as e:
            st.error(f"Erro ao carregar JSON: {e}")

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        municipio_nome, promotoria = "Não identificado", "Não identificada"
        end_upper = self.remover_acentos(str(endereco).upper())
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome, promotoria = info["municipio_oficial"], info["promotoria"]
                break

        # CHAMADA MISTRAL - CONFIGURAÇÃO DO PROMPT COM REGRAS DE BAIRRO E LIMITE
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        
        prompt = (
            f"Endereço: {endereco}\n"
            f"Relato: {denuncia}\n\n"
            f"Catálogo: {catalogo}\n\n"
            "Retorne APENAS um JSON (chaves: tema, subtema, empresa, resumo).\n"
            "REGRAS PARA O CAMPO 'resumo':\n"
            "1. Identifique o BAIRRO no endereço e comece o resumo por ele.\n"
            "2. O resumo deve ter NO MÁXIMO 10 palavras no total."
        )

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            dados_ia = json.loads(response.choices[0].message.content)
        except Exception as e:
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
            "empresa": str(dados_ia.get("empresa")).title(),
            "vencedor": vencedor, 
            "responsavel": responsavel
        }

        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json=dados_final, timeout=10)
            except:
                pass
        
        return dados_final
