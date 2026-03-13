# -*- coding: utf-8 -*-
import json
import requests
import os
import unicodedata
import streamlit as st
from datetime import datetime

# SISTEMA DE IMPORTAÇÃO SEGURO PARA MISTRAL
try:
    from mistralai import Mistral
except ImportError:
    try:
        from mistralai.client import MistralClient as Mistral
    except ImportError:
        st.error("Erro crítico: A biblioteca 'mistralai' não foi instalada corretamente.")

class ClassificadorDenuncias:
    def __init__(self):
        # 1. BUSCA DA KEY DA MISTRAL
        api_key = os.environ.get("MISTRAL_API_KEY") or st.secrets.get("MISTRAL_API_KEY", "")

        if api_key:
            try:
                self.client = Mistral(api_key=api_key)
                self.model = "mistral-small-latest" 
            except Exception as e:
                st.error(f"Erro ao inicializar Mistral: {e}")
        else:
            st.error("ERRO: MISTRAL_API_KEY não encontrada no Render.")

        # 2. WEBHOOK DA PLANILHA (O NOVO LINK QUE VOCÊ COPIOU)
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
            st.error(f"Erro ao carregar arquivos JSON: {e}")

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # Identificação de Município e Promotoria
        municipio_nome, promotoria = "Não identificado", "Não identificada"
        end_upper = self.remover_acentos(str(endereco).upper())
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome, promotoria = info["municipio_
