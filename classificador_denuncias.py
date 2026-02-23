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
        # 1. Definição de Caminhos
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_path, "saro_database.db")
        
        # 2. Configuração IA Gemini (Versão Gratuita)
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ Erro: GOOGLE_API_KEY não encontrada nos Secrets do Streamlit.")
            st.stop()
            
        genai.configure(api_key=api_key)
        # Atualizado para a versão latest conforme solicitado
        self.model = genai.GenerativeModel('gemini-flash-latest')
        
        # 3. Inicializar Bases e Banco
        self.carregar_bases()
        self.inicializar_banco()

    def carregar_bases(self):
        """Carrega os arquivos JSON de apoio (Municípios e Temas)"""
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
            st.error(f"Erro ao carregar arquivos JSON: {e}")

    def inicializar_banco(self):
        """Cria a tabela SQLite local se não existir"""
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

    def extrair_rua_bairro(self, endereco):
        """Lógica para identificar Rua e Bairro no texto do endereço"""
        if not endereco:
            return "Rua não informada", "Bairro não informado"

        # Limpeza e separação por vírgula ou hífen
        end_limpo = endereco.replace(' - ', ',').replace('-', ',')
        partes = [p.strip() for p in end_limpo.split(',') if p.strip()]
        
        rua = "Rua não informada"
        bairro = "Bairro não informado"

        # Tenta pegar a rua (primeira parte)
        if len(partes) >= 1:
            rua = partes[0]
        
        # Tenta achar o bairro
        if len(partes) >= 2:
            # Se a última parte for estado (ex: RJ), tenta a anterior para o bairro
            if partes[-1].upper() in ["RJ", "RIO DE JANEIRO", "BRASIL"] and len(partes) >= 3:
                bairro = partes[-2]
            else:
                bairro = partes[1] if len(partes) == 2 else partes[-1]
        
        return rua, bairro

    def salvar_no_banco(self, d):
        """Grava os dados processados no banco SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ouvidorias (num_com, num_mprj, data, municipio, promotoria, tema, subtema, empresa, denuncia, resumo, vencedor, responsavel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (d['num_com'], d['num_mprj'], d['data'], d['municipio'], d['promotoria'], d['tema'], d['subtema'], d['empresa'], d['denuncia'], d['resumo'], d['vencedor'], d['responsavel']))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # 1. Identificar Município e Promotoria
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. Extrair Rua e Bairro do endereço fornecido
        rua_detectada, bairro_detectado = self.extrair_rua_bairro(endereco)

        # 3. Classificação com IA Gemini
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = (f"Classifique a denúncia: {denuncia}. "
                  f"Use estritamente este catálogo: {catalogo}. "
                  f"Retorne APENAS um JSON com as chaves: tema, subtema, empresa, resumo (máx 10 palavras).")
        
        try:
            response = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            dados_ia = json.loads(response.text)
        except:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "N/D", "resumo": "Erro no processamento da IA."}

        # 4. Formatar Resumo com Rua/Bairro conforme solicitado
        resumo_ia = dados_ia.get("resumo", "Sem resumo").strip()
        if not resumo_ia.endswith('.'):
            resumo_ia += '.'
        
        resumo_final = f"{resumo_ia} {rua_detectada} / {bairro_detectado}"

        # 5. Montagem do Pacote Final
        dados_final = {
            "num_com": num_com, 
            "num_mprj": num_mprj, 
            "promotoria": promotoria,
            "municipio": municipio_nome, 
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "denuncia": denuncia, 
            "resumo": resumo_final,
            "tema": dados_ia.get("tema"), 
            "subtema": dados_ia.get("subtema"),
            "empresa": str(dados_ia.get("empresa")).title(),
            "vencedor": vencedor, 
            "responsavel": responsavel
        }

        # 6. Salvar no Banco
        sucesso = self.salvar_no_banco(dados_final)
        return dados_final, sucesso
