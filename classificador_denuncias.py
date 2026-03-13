# -*- coding: utf-8 -*-
import json
import requests
import os
import unicodedata
import streamlit as st
from datetime import datetime
from mistralai import Mistral

class ClassificadorDenuncias:
    def __init__(self):
        api_key = os.environ.get("MISTRAL_API_KEY") or st.secrets.get("MISTRAL_API_KEY", "")
        self.client = None
        if api_key:
            try:
                self.client = Mistral(api_key=api_key)
                self.model = "mistral-small-latest"
            except Exception as e:
                st.error(f"Erro Mistral: {e}")

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
            st.error(f"Erro bases: {e}")

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco).upper()
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = (
            f"Endereço: {endereco}\nRelato: {denuncia}\n\nCatálogo: {catalogo}\n\n"
            "Retorne APENAS JSON com as chaves: tema, subtema, empresa, bairro, resumo.\n"
            "Regras: 1. No campo 'bairro', extraia apenas o nome do bairro do endereço.\n"
            "2. No campo 'resumo', inicie pelo bairro e limite a 10 palavras."
        )

        dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "N/D", "bairro": "Não identificado", "resumo": "Erro IA"}
        
        if self.client:
            try:
                response = self.client.chat.complete(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                dados_ia = json.loads(response.choices[0].message.content)
            except:
                pass

        dados_final = {
            "num_com": str(num_com),
            "num_mprj": str(num_mprj),
            "promotoria": promotoria,
            "municipio": municipio_nome,
            "bairro_ouvidoria": dados_ia.get("bairro", "Não identificado"), # NOVA CHAVE
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
                requests.post(self.webhook_url, json=dados_final, timeout=15)
            except:
                pass
        
        return dados_final
