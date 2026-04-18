import sqlite3
import os
import uuid
import sys

# Adiciona o diretório raiz ao path para importar config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BANCO_PATH, BANCO_DIR

def gerar_id_sequencial():
    from datetime import datetime
    ano_atual = datetime.now().year
    conn = sqlite3.connect(BANCO_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM CASOS WHERE id LIKE ?", (f"%_{ano_atual}",))
    ids = cursor.fetchall()
    conn.close()
    
    proximo_numero = 1
    if ids:
        numeros = []
        for (id_str,) in ids:
            try:
                # Tenta pegar apenas a parte numérica antes do "_"
                num_parte = id_str.split('_')[0]
                if num_parte.isdigit():
                    numeros.append(int(num_parte))
            except (ValueError, IndexError):
                continue
        if numeros:
            proximo_numero = max(numeros) + 1
            
    return f"{proximo_numero:03d}_{ano_atual}"

def criar_banco():
    """
    Cria o banco de dados SQLite e a tabela CASOS, caso não existam.
    A tabela CASOS armazena todas as informações de um caso jurídico:
    dados do cliente, relato, classificação da IA, prioridade e anexos.
    """
    os.makedirs(BANCO_DIR, exist_ok=True)
    conn = sqlite3.connect(BANCO_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CASOS (
            id            TEXT    PRIMARY KEY,
            nome_cliente  TEXT    NOT NULL,
            email         TEXT,
            whatsapp      TEXT,
            relato        TEXT    NOT NULL,
            tipo_caso     TEXT,
            prioridade    TEXT,
            anexos        TEXT, -- Armazena caminhos dos arquivos, separados por vírgula
            data_cadastro DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()
    print("[Banco] Banco de dados inicializado com sucesso.")

def inserir_caso(id_caso, nome_cliente, email, whatsapp, relato, tipo_caso, prioridade, anexos):
    """
    Insere um novo caso jurídico no banco de dados.
    """
    conn = sqlite3.connect(BANCO_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CASOS (id, nome_cliente, email, whatsapp, relato, tipo_caso, prioridade, anexos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (id_caso, nome_cliente, email, whatsapp, relato, tipo_caso, prioridade, anexos))
    conn.commit()
    conn.close()
    return id_caso

def listar_casos():
    """
    Retorna todos os casos cadastrados no banco de dados.
    """
    conn = sqlite3.connect(BANCO_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome_cliente, email, whatsapp, relato,
               tipo_caso, prioridade, anexos, data_cadastro
        FROM CASOS
        ORDER BY data_cadastro DESC
    """)
    casos = cursor.fetchall()
    conn.close()
    return casos

def buscar_caso_por_id(caso_id):
    """
    Busca um caso específico pelo seu ID.
    """
    conn = sqlite3.connect(BANCO_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome_cliente, email, whatsapp, relato,
               tipo_caso, prioridade, anexos, data_cadastro
        FROM CASOS
        WHERE id = ?
    """, (caso_id,))
    caso = cursor.fetchone()
    conn.close()
    return caso
