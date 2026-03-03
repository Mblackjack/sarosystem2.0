# -*- coding: utf-8 -*-
import json
import os
import sqlite3
import unicodedata
import streamlit as st
import google.generativeai as genai
from datetime import datetime

class ClassificadorDenuncias:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_path, "saro_database.db")
        
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                # Modelo exato solicitado
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            else:
                st.error("Chave GOOGLE_API_KEY não encontrada nos Secrets.")
        except Exception as e:
            st.error(f"Erro ao configurar IA: {e}")
        
        self.carregar_bases()
        self.inicializar_banco()

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
        except:
            self.temas_subtemas = {}
            self.municipio_para_promotoria = {}

    def inicializar_banco(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ouvidorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                num_com TEXT, num_mprj TEXT, data TEXT,
                municipio TEXT, promotoria TEXT, tema TEXT,
                subtema TEXT, empresa TEXT, denuncia TEXT,
                resumo TEXT, vencedor TEXT, responsavel TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        
        # PROMPT REFORÇADO PARA EVITAR ERROS DE JSON
        prompt = (
            f"Você é um classificador de ouvidorias do MPRJ.\n"
            f"DADOS:\n- Endereço: {endereco}\n- Denúncia: {denuncia}\n\n"
            f"CATÁLOGO: {catalogo}\n\n"
            f"REGRAS:\n"
            f"1. Extraia Rua e Bairro apenas do Endereço acima.\n"
            f"2. Resuma a denúncia em 10 palavras.\n"
            f"3. Responda APENAS o JSON no formato:\n"
            f'{{"tema": "...", "subtema": "...", "empresa": "...", "resumo_curto": "...", "rua": "...", "bairro": "..."}}'
        )
        
        try:
            response = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            dados_ia = json.loads(response.text)
            
            res_base = dados_ia.get("resumo_curto", "Sem resumo").strip()
            if not res_base.endswith('.'): res_base += '.'
            
            rua = dados_ia.get("rua", "Não informada")
            bairro = dados_ia.get("bairro", "Não informado")
            resumo_final = f"{res_base} Rua: {rua}/Bairro: {bairro}"
        except Exception as e:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "N/D"}
            resumo_final = f"Erro na IA: {str(e)[:50]}... Rua: Não identificada/Bairro: Não identificado"

        dados_final = {
            "num_com": str(num_com), "num_mprj": str(num_mprj), "promotoria": promotoria,
            "municipio": municipio_nome, "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "denuncia": denuncia, "resumo": resumo_final,
            "tema": dados_ia.get("tema", "Outros"), "subtema": dados_ia.get("subtema", "Geral"),
            "empresa": str(dados_ia.get("empresa", "N/D")).title(),
            "vencedor": vencedor, "responsavel": responsavel
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO ouvidorias (num_com, num_mprj, data, municipio, promotoria, tema, subtema, empresa, denuncia, resumo, vencedor, responsavel)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', 
                            (num_com, num_mprj, dados_final['data'], municipio_nome, promotoria, 
                             dados_final['tema'], dados_final['subtema'], dados_final['empresa'], 
                             denuncia, resumo_final, vencedor, responsavel))
            conn.commit()
            conn.close()
            sucesso = True
        except:
            sucesso = False

        return dados_final, sucesso
