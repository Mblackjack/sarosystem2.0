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
        
        # Configuração do Gemini 1.5 Flash Latest
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
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
        # 1. Localidade (Busca interna por Município/Promotoria)
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. IA para Classificação e Extração de Rua/Bairro do campo Endereço
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = (
            f"Você é um assistente do MPRJ.\n\n"
            f"ENDEREÇO FORNECIDO: {endereco}\n"
            f"DENÚNCIA: {denuncia}\n\n"
            f"TAREFAS:\n"
            f"1. Extraia a RUA e o BAIRRO exclusivamente do 'ENDEREÇO FORNECIDO'.\n"
            f"2. Classifique a denúncia conforme o catálogo: {catalogo}\n\n"
            f"Responda APENAS um JSON com:\n"
            f"'tema', 'subtema', 'empresa', 'resumo_curto' (máx 10 palavras),\n"
            f"'rua_ext' (se não houver, 'Rua não informada'), 'bairro_ext' (se não houver, 'Bairro não informado')."
        )
        
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            dados_ia = json.loads(response.text)
            
            # Formatação: "Resumo. Rua: X/Bairro: Y"
            res_ia = dados_ia.get("resumo_curto", "").strip()
            if not res_ia.endswith('.'): res_ia += '.'
            
            rua = dados_ia.get("rua_ext", "Rua não informada")
            bairro = dados_ia.get("bairro_ext", "Bairro não informado")
            resumo_final = f"{res_ia} Rua: {rua}/Bairro: {bairro}"
        except:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "N/D"}
            resumo_final = "IA temporariamente indisponível."

        # 3. Montagem do Dicionário Final
        dados_final = {
            "num_com": str(num_com), "num_mprj": str(num_mprj), "promotoria": promotoria,
            "municipio": municipio_nome, "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "denuncia": denuncia, "resumo": resumo_final,
            "tema": dados_ia.get("tema", "Outros"), "subtema": dados_ia.get("subtema", "Geral"),
            "empresa": str(dados_ia.get("empresa", "N/D")).title(),
            "vencedor": vencedor, "responsavel": responsavel
        }

        # 4. Salvar no Banco Interno (SQLite)
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
