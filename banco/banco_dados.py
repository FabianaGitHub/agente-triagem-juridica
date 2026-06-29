import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Detecta automaticamente se está no Render (PostgreSQL) ou local (SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL")
USANDO_POSTGRES = DATABASE_URL is not None

if USANDO_POSTGRES:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3
    from config import BANCO_PATH, BANCO_DIR


def _conectar():
    """Retorna uma conexão com o banco correto conforme o ambiente."""
    if USANDO_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(BANCO_PATH)


def criar_banco():
    """
    Cria a tabela CASOS se não existir.
    Funciona tanto no PostgreSQL (Render) quanto no SQLite (local).
    """
    if not USANDO_POSTGRES:
        os.makedirs(BANCO_DIR, exist_ok=True)

    conn = _conectar()
    cursor = conn.cursor()

    if USANDO_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS casos (
                id            TEXT    PRIMARY KEY,
                nome_cliente  TEXT    NOT NULL,
                email         TEXT,
                whatsapp      TEXT,
                relato        TEXT    NOT NULL,
                tipo_caso     TEXT,
                prioridade    TEXT,
                encaminhamento TEXT,
                anexos        TEXT,
                data_cadastro TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CASOS (
                id            TEXT    PRIMARY KEY,
                nome_cliente  TEXT    NOT NULL,
                email         TEXT,
                whatsapp      TEXT,
                relato        TEXT    NOT NULL,
                tipo_caso     TEXT,
                prioridade    TEXT,
                encaminhamento TEXT,
                anexos        TEXT,
                data_cadastro DATETIME DEFAULT (datetime('now', 'localtime'))
            )
        """)

    conn.commit()

    # Migração: adiciona coluna encaminhamento se não existir (SQLite)
    if not USANDO_POSTGRES:
        try:
            cursor.execute("ALTER TABLE CASOS ADD COLUMN encaminhamento TEXT")
            conn.commit()
        except Exception:
            pass  # coluna já existe

    conn.close()
    print("[Banco] Inicializado com sucesso.")


def gerar_id_sequencial():
    """Gera um ID único no formato 001_2026."""
    ano_atual = datetime.now().year
    conn = _conectar()
    cursor = conn.cursor()

    if USANDO_POSTGRES:
        cursor.execute(
            "SELECT id FROM casos WHERE id LIKE %s",
            (f"%_{ano_atual}",)
        )
    else:
        cursor.execute(
            "SELECT id FROM CASOS WHERE id LIKE ?",
            (f"%_{ano_atual}",)
        )

    ids = cursor.fetchall()
    conn.close()

    proximo_numero = 1
    if ids:
        numeros = []
        for (id_str,) in ids:
            try:
                num_parte = id_str.split('_')[0]
                if num_parte.isdigit():
                    numeros.append(int(num_parte))
            except (ValueError, IndexError):
                continue
        if numeros:
            proximo_numero = max(numeros) + 1

    return f"{proximo_numero:03d}_{ano_atual}"


def inserir_caso(id_caso, nome_cliente, email, whatsapp,
                 relato, tipo_caso, prioridade, anexos,
                 encaminhamento="não informado"):
    """Insere um novo caso no banco."""
    conn = _conectar()
    cursor = conn.cursor()

    if USANDO_POSTGRES:
        cursor.execute("""
            INSERT INTO casos
                (id, nome_cliente, email, whatsapp, relato,
                 tipo_caso, prioridade, encaminhamento, anexos)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (id_caso, nome_cliente, email, whatsapp, relato,
              tipo_caso, prioridade, encaminhamento, anexos))
    else:
        cursor.execute("""
            INSERT INTO CASOS
                (id, nome_cliente, email, whatsapp, relato,
                 tipo_caso, prioridade, encaminhamento, anexos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_caso, nome_cliente, email, whatsapp, relato,
              tipo_caso, prioridade, encaminhamento, anexos))

    conn.commit()
    conn.close()
    return id_caso


def salvar_caso(protocolo, descricao, classificacao,
                prioridade, acao_sugerida, whatsapp=''):
    """
    Função usada pela integração WhatsApp (integracao_whatsapp.py).
    Adapta os parâmetros e chama inserir_caso.
    """
    return inserir_caso(
        id_caso=protocolo,
        nome_cliente="Via WhatsApp",
        email="",
        whatsapp=whatsapp,
        relato=descricao,
        tipo_caso=classificacao,
        prioridade=prioridade,
        anexos="",
        encaminhamento=acao_sugerida
    )


def listar_casos():
    """Retorna todos os casos ordenados do mais recente para o mais antigo."""
    conn = _conectar()
    cursor = conn.cursor()

    tabela = "casos" if USANDO_POSTGRES else "CASOS"
    cursor.execute(f"""
        SELECT id, nome_cliente, email, whatsapp, relato,
               tipo_caso, prioridade, anexos, data_cadastro
        FROM {tabela}
        ORDER BY data_cadastro DESC
    """)

    casos = cursor.fetchall()
    conn.close()
    return casos


def buscar_caso_por_id(caso_id):
    """Busca um caso específico pelo ID."""
    conn = _conectar()
    cursor = conn.cursor()

    if USANDO_POSTGRES:
        cursor.execute("""
            SELECT id, nome_cliente, email, whatsapp, relato,
                   tipo_caso, prioridade, anexos, data_cadastro
            FROM casos WHERE id = %s
        """, (caso_id,))
    else:
        cursor.execute("""
            SELECT id, nome_cliente, email, whatsapp, relato,
                   tipo_caso, prioridade, anexos, data_cadastro
            FROM CASOS WHERE id = ?
        """, (caso_id,))

    caso = cursor.fetchone()
    conn.close()
    return caso
