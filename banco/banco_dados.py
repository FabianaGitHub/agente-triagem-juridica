import os
import sys
import json
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

    # Tabela de consentimentos LGPD
    if USANDO_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consentimentos (
                whatsapp          TEXT PRIMARY KEY,
                data_consentimento TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes_ativas (
                whatsapp      TEXT PRIMARY KEY,
                dados_json    TEXT NOT NULL,
                atualizado_em TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consentimentos (
                whatsapp          TEXT PRIMARY KEY,
                data_consentimento DATETIME DEFAULT (datetime('now','localtime'))
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes_ativas (
                whatsapp      TEXT PRIMARY KEY,
                dados_json    TEXT NOT NULL,
                atualizado_em DATETIME DEFAULT (datetime('now','localtime'))
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


# ── Consentimentos ────────────────────────────────────────────────────────────

def registrar_consentimento(numero):
    conn = _conectar()
    cursor = conn.cursor()
    tabela = "consentimentos"
    if USANDO_POSTGRES:
        cursor.execute(
            "INSERT INTO consentimentos (whatsapp) VALUES (%s) ON CONFLICT DO NOTHING",
            (numero,)
        )
    else:
        cursor.execute(
            "INSERT OR IGNORE INTO consentimentos (whatsapp) VALUES (?)",
            (numero,)
        )
    conn.commit()
    conn.close()


def verificar_consentimento(numero):
    conn = _conectar()
    cursor = conn.cursor()
    if USANDO_POSTGRES:
        cursor.execute("SELECT 1 FROM consentimentos WHERE whatsapp = %s", (numero,))
    else:
        cursor.execute("SELECT 1 FROM consentimentos WHERE whatsapp = ?", (numero,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe


def revogar_consentimento(numero):
    conn = _conectar()
    cursor = conn.cursor()
    if USANDO_POSTGRES:
        cursor.execute("DELETE FROM consentimentos WHERE whatsapp = %s", (numero,))
    else:
        cursor.execute("DELETE FROM consentimentos WHERE whatsapp = ?", (numero,))
    conn.commit()
    conn.close()


# ── Sessões ativas ────────────────────────────────────────────────────────────

def salvar_sessao(numero, dados):
    """Persiste a sessão ativa no banco (sem o campo 'perguntas', reconstituído no load)."""
    dados_sem_perguntas = {k: v for k, v in dados.items() if k != 'perguntas'}
    dados_json = json.dumps(dados_sem_perguntas, ensure_ascii=False)
    conn = _conectar()
    cursor = conn.cursor()
    if USANDO_POSTGRES:
        cursor.execute("""
            INSERT INTO sessoes_ativas (whatsapp, dados_json, atualizado_em)
            VALUES (%s, %s, NOW())
            ON CONFLICT (whatsapp) DO UPDATE
            SET dados_json = EXCLUDED.dados_json, atualizado_em = NOW()
        """, (numero, dados_json))
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO sessoes_ativas (whatsapp, dados_json, atualizado_em)
            VALUES (?, ?, datetime('now','localtime'))
        """, (numero, dados_json))
    conn.commit()
    conn.close()


def obter_sessao(numero):
    """Retorna o dict da sessão ou None se não existir."""
    conn = _conectar()
    cursor = conn.cursor()
    if USANDO_POSTGRES:
        cursor.execute(
            "SELECT dados_json FROM sessoes_ativas WHERE whatsapp = %s", (numero,)
        )
    else:
        cursor.execute(
            "SELECT dados_json FROM sessoes_ativas WHERE whatsapp = ?", (numero,)
        )
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None


def deletar_sessao(numero):
    conn = _conectar()
    cursor = conn.cursor()
    if USANDO_POSTGRES:
        cursor.execute("DELETE FROM sessoes_ativas WHERE whatsapp = %s", (numero,))
    else:
        cursor.execute("DELETE FROM sessoes_ativas WHERE whatsapp = ?", (numero,))
    conn.commit()
    conn.close()
