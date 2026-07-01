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

    # Tabela de advogados cadastrados
    if USANDO_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advogados (
                id            SERIAL PRIMARY KEY,
                nome          TEXT NOT NULL,
                email         TEXT NOT NULL,
                whatsapp      TEXT,
                oab_numero    TEXT,
                oab_uf        TEXT,
                areas_atuacao TEXT DEFAULT '[]',
                ativo         BOOLEAN DEFAULT TRUE,
                cadastrado_em TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advogados (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nome          TEXT NOT NULL,
                email         TEXT NOT NULL,
                whatsapp      TEXT,
                oab_numero    TEXT,
                oab_uf        TEXT,
                areas_atuacao TEXT DEFAULT '[]',
                ativo         INTEGER DEFAULT 1,
                cadastrado_em DATETIME DEFAULT (datetime('now','localtime'))
            )
        """)

    # Tabela de log de mensagens (monitoramento de conversas)
    if USANDO_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensagens (
                id         SERIAL PRIMARY KEY,
                whatsapp   TEXT NOT NULL,
                direcao    TEXT NOT NULL,
                texto      TEXT NOT NULL,
                data_hora  TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensagens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                whatsapp   TEXT NOT NULL,
                direcao    TEXT NOT NULL,
                texto      TEXT NOT NULL,
                data_hora  DATETIME DEFAULT (datetime('now','localtime'))
            )
        """)

    conn.commit()
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
                prioridade, acao_sugerida, whatsapp='', nome_cliente='Via WhatsApp'):
    """
    Função usada pela integração WhatsApp (integracao_whatsapp.py).
    Adapta os parâmetros e chama inserir_caso.
    """
    return inserir_caso(
        id_caso=protocolo,
        nome_cliente=nome_cliente or "Via WhatsApp",
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


# ── Advogados ─────────────────────────────────────────────────────────────────

def criar_advogado(nome, email, whatsapp, oab_numero, oab_uf, areas_atuacao):
    """Insere um novo advogado. areas_atuacao é uma lista Python."""
    areas_json = json.dumps(areas_atuacao, ensure_ascii=False)
    conn = _conectar()
    cursor = conn.cursor()
    if USANDO_POSTGRES:
        cursor.execute("""
            INSERT INTO advogados (nome, email, whatsapp, oab_numero, oab_uf, areas_atuacao)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nome, email, whatsapp, oab_numero, oab_uf, areas_json))
    else:
        cursor.execute("""
            INSERT INTO advogados (nome, email, whatsapp, oab_numero, oab_uf, areas_atuacao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, email, whatsapp, oab_numero, oab_uf, areas_json))
    conn.commit()
    conn.close()


def listar_advogados():
    """Retorna lista de dicts com todos os advogados."""
    conn = _conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, email, whatsapp, oab_numero, oab_uf, areas_atuacao, ativo, cadastrado_em
        FROM advogados ORDER BY nome
    """)
    rows = cursor.fetchall()
    conn.close()
    resultado = []
    for row in rows:
        id_, nome, email, whatsapp, oab_num, oab_uf, areas_json, ativo, cadastrado_em = row
        try:
            areas = json.loads(areas_json or '[]')
        except Exception:
            areas = []
        resultado.append({
            'id': id_,
            'nome': nome,
            'email': email,
            'whatsapp': whatsapp or '',
            'oab_numero': oab_num or '',
            'oab_uf': oab_uf or '',
            'areas': areas,
            'ativo': bool(ativo),
            'cadastrado_em': cadastrado_em,
        })
    return resultado


def buscar_advogado_por_area(area):
    """Retorna o primeiro advogado ativo que atende a área, ou None."""
    advogados = listar_advogados()
    ativos = [a for a in advogados if a['ativo']]
    for adv in ativos:
        if not adv['areas'] or area in adv['areas']:
            return adv
    return None


# ── Mensagens (monitoramento de conversas) ───────────────────────────────────

def registrar_mensagem(whatsapp, direcao, texto):
    """Grava uma mensagem recebida ('entrada') ou enviada ('saida') pelo bot."""
    conn = _conectar()
    cursor = conn.cursor()
    if USANDO_POSTGRES:
        cursor.execute(
            "INSERT INTO mensagens (whatsapp, direcao, texto) VALUES (%s, %s, %s)",
            (whatsapp, direcao, texto)
        )
    else:
        cursor.execute(
            "INSERT INTO mensagens (whatsapp, direcao, texto) VALUES (?, ?, ?)",
            (whatsapp, direcao, texto)
        )
    conn.commit()
    conn.close()


def listar_conversas():
    """Retorna um contato por linha com a data da última mensagem, mais recentes primeiro."""
    conn = _conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT whatsapp, MAX(data_hora) as ultima, COUNT(*) as total
        FROM mensagens
        GROUP BY whatsapp
        ORDER BY ultima DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{'whatsapp': r[0], 'ultima': r[1], 'total': r[2]} for r in rows]


def buscar_conversa_por_numero(whatsapp):
    """Retorna todas as mensagens de um número em ordem cronológica."""
    conn = _conectar()
    cursor = conn.cursor()
    if USANDO_POSTGRES:
        cursor.execute(
            "SELECT direcao, texto, data_hora FROM mensagens WHERE whatsapp = %s ORDER BY data_hora ASC",
            (whatsapp,)
        )
    else:
        cursor.execute(
            "SELECT direcao, texto, data_hora FROM mensagens WHERE whatsapp = ? ORDER BY data_hora ASC",
            (whatsapp,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [{'direcao': r[0], 'texto': r[1], 'data_hora': r[2]} for r in rows]


def atualizar_status_advogado(adv_id, ativo):
    """Ativa ou desativa um advogado."""
    conn = _conectar()
    cursor = conn.cursor()
    valor = True if USANDO_POSTGRES else (1 if ativo else 0)
    if not ativo:
        valor = False if USANDO_POSTGRES else 0
    if USANDO_POSTGRES:
        cursor.execute("UPDATE advogados SET ativo = %s WHERE id = %s", (valor, adv_id))
    else:
        cursor.execute("UPDATE advogados SET ativo = ? WHERE id = ?", (valor, adv_id))
    conn.commit()
    conn.close()
