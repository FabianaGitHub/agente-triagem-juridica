import base64
import os
import requests as _http
from datetime import date, datetime
from functools import wraps
from urllib.parse import quote_plus
from werkzeug.utils import secure_filename
from flask import (Flask, request, session, redirect,
                   url_for, render_template, send_file, send_from_directory)
from ia.motor_decisao import MotorDecisaoJuridica as MotorDecisao
from ia.base_conhecimento import (
    obter_perguntas, CEJUSC_INFO, PROCON_INFO, JEC_INFO, ANS_INFO, MEU_INSS_INFO, BC_INFO
)
from banco.banco_dados import (salvar_caso, criar_banco, gerar_id_sequencial,
                               registrar_consentimento, verificar_consentimento,
                               revogar_consentimento, salvar_sessao, obter_sessao,
                               deletar_sessao, criar_advogado, listar_advogados,
                               buscar_advogado_por_area, atualizar_status_advogado,
                               registrar_mensagem, listar_conversas,
                               buscar_conversa_por_numero,
                               registrar_sugestao, listar_sugestoes_pendentes,
                               listar_keywords_aprovadas, aprovar_sugestao,
                               ignorar_sugestao,
                               atualizar_caso, deletar_caso, adicionar_upload_caso,
                               buscar_caso_por_id)

AREAS_JURIDICAS = [
    'Direito do Consumidor',
    'Direito Trabalhista',
    'Direito de Família',
    'Direito Bancário',
    'Previdência Social',
]

UF_LISTA = [
    'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
    'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO',
]

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
_STATIC_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
app = Flask(__name__, template_folder=_TEMPLATE_DIR, static_folder=_STATIC_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'acessus-juridico-2026')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE']   = os.environ.get('DATABASE_URL') is not None  # True só no Render (HTTPS)

motor = MotorDecisao()
criar_banco()

ADVOGADOS_SENHA = os.environ.get('ADVOGADOS_SENHA', 'acessus2026')

# ── Diretórios de mídia ───────────────────────────────────────────────────────
_BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUDIO_DIR   = os.path.join(_BASE_DIR, 'audios')
_UPLOAD_DIR  = os.path.join(_BASE_DIR, 'uploads')
os.makedirs(_AUDIO_DIR, exist_ok=True)
os.makedirs(_UPLOAD_DIR, exist_ok=True)

_EXTENSOES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}

def _extensao_permitida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _EXTENSOES_PERMITIDAS

# ── Evolution API ─────────────────────────────────────────────────────────────
_EVO_URL      = os.environ.get('EVOLUTION_API_URL',      'http://localhost:8080')
_EVO_KEY      = os.environ.get('EVOLUTION_API_KEY',      '')
_EVO_INSTANCE = os.environ.get('EVOLUTION_INSTANCE',     'acessus')

def _normalizar_numero(raw):
    """Extrai apenas os dígitos do número (ex: '5519999@s.whatsapp.net' → '5519999')."""
    return raw.replace('@s.whatsapp.net', '').replace('@c.us', '').replace('+', '').strip()

def _enviar_mensagem(numero, texto):
    """Envia mensagem de texto via Evolution API."""
    try:
        _http.post(
            f"{_EVO_URL}/message/sendText/{_EVO_INSTANCE}",
            json={"number": _normalizar_numero(numero), "text": texto},
            headers={"apikey": _EVO_KEY, "Content-Type": "application/json"},
            timeout=10,
        )
    except Exception as e:
        print(f"[Evolution API] Erro ao enviar para {numero}: {e}")


def _baixar_audio_evo(msg_obj, numero):
    """Baixa áudio via Evolution API e salva em disco. Retorna (caminho_abs, caminho_rel) ou (None, None)."""
    try:
        r = _http.post(
            f"{_EVO_URL}/chat/getBase64FromMediaMessage/{_EVO_INSTANCE}",
            json={"message": msg_obj},
            headers={"apikey": _EVO_KEY},
            timeout=30,
        )
        if r.status_code != 200:
            return None, None
        dados = r.json()
        b64 = dados.get("base64") or dados.get("data", {}).get("base64", "")
        if not b64:
            return None, None

        numero_limpo = _normalizar_numero(numero)
        pasta_abs = os.path.join(_AUDIO_DIR, numero_limpo)
        os.makedirs(pasta_abs, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"{timestamp}.ogg"
        caminho_abs = os.path.join(pasta_abs, nome_arquivo)
        with open(caminho_abs, 'wb') as f:
            f.write(base64.b64decode(b64))
        caminho_rel = os.path.join(numero_limpo, nome_arquivo)
        return caminho_abs, caminho_rel
    except Exception as e:
        print(f"[Áudio] Erro ao baixar: {e}")
        return None, None


_whisper_model = None

def _transcrever_audio(caminho):
    """Transcreve áudio com faster-whisper tiny. Retorna texto ou None."""
    global _whisper_model
    try:
        if _whisper_model is None:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = _whisper_model.transcribe(caminho, language="pt")
        return " ".join(s.text.strip() for s in segments).strip() or None
    except Exception as e:
        print(f"[Áudio] Erro na transcrição: {e}")
        return None

# ── Sessões e consentimentos persistidos no banco ────────────────────────────
# Substituem os dicts/sets em memória — sobrevivem a reinícios do servidor.

def _get_sessao(numero):
    dados = obter_sessao(numero)
    if dados and 'area' in dados and 'sub_area' in dados:
        # Reconstitui exatamente como iniciar_questionario monta:
        # pergunta_nome sempre na posição 0, seguida das perguntas da área
        pergunta_nome = {
            "chave": "nome_completo",
            "texto": "Para registrar seu caso, preciso do seu *nome completo*."
        }
        perguntas_area = obter_perguntas(dados['area'], dados['sub_area'])
        dados['perguntas'] = [pergunta_nome] + perguntas_area
    return dados or {}

def _set_sessao(numero, dados):
    salvar_sessao(numero, dados)

def _del_sessao(numero):
    deletar_sessao(numero)

# ── Histórico diário ────────────────────────────────────────────────────────
# historico[numero][data][area] = quantidade de perguntas
historico = {}

# ── Modo de teste ────────────────────────────────────────────────────────────
# MODO_TESTE = True  → sem limite de relatos por dia, comando REINICIAR ativo
# MODO_TESTE = False → limites normais de produção (alterar aqui após os testes)
MODO_TESTE = os.environ.get('MODO_TESTE', 'false').lower() == 'true'

# ── Constantes WhatsApp ──────────────────────────────────────────────────────
LIMITE_AVISO    = 2
LIMITE_BLOQUEIO = 3

DEFENSORIA_CAMPINAS = (
    "🏛️ *Defensoria Pública de Campinas*\n"
    "📍 Rua Regente Feijó, 1138 — Centro, Campinas/SP\n"
    "📞 (19) 3236-8600\n"
    "🕐 Segunda a sexta, das 8h às 17h\n\n"
    "Para outras cidades de SP: www.defensoria.sp.def.br\n"
    "Para qualquer cidade do Brasil: ligue *129* (gratuito)"
)

DISCLAIMER = (
    "\n\n_⚠️ Este sistema fornece informações jurídicas de caráter "
    "geral com base na legislação brasileira. Não constitui assessoria "
    "jurídica, não substitui advogado e não deve ser utilizado como "
    "documento ou prova em qualquer processo._"
)

def _montar_termo(nome_whatsapp=''):
    saudacao = f"Olá, *{nome_whatsapp}*! 👋\n\n" if nome_whatsapp else "Olá! 👋\n\n"
    return (
        saudacao +
        "Antes de começar, preciso do seu consentimento sobre como "
        "seus dados serão usados.\n\n"
        "📋 *Termo de Consentimento — Agente Jurídico*\n\n"
        "Ao utilizar este serviço, você autoriza:\n\n"
        "✅ A coleta do seu número de WhatsApp e das mensagens enviadas\n"
        "✅ O uso dessas informações para orientação jurídica e registro do seu caso\n"
        "✅ O compartilhamento com advogados parceiros *somente* se você "
        "solicitar encaminhamento\n\n"
        "🔒 *Seus dados são protegidos pela Lei Geral de Proteção de Dados "
        "(LGPD — Lei 13.709/2018)*\n\n"
        "Este serviço é *gratuito* e fornece *informações jurídicas gerais*. "
        "Não substitui atendimento com advogado.\n\n"
        "Você pode parar de usar o serviço a qualquer momento.\n\n"
        "---\n"
        "*Você concorda com os termos acima?*\n\n"
        "1️⃣ Sim, concordo — quero continuar\n"
        "2️⃣ Não concordo — quero sair\n\n"
        "_Responda com 1 ou 2._"
    )

# Cores Bootstrap por área (usadas nos templates)
_COR_AREA = {
    'Direito do Consumidor': 'primary',
    'Direito Trabalhista':   'warning',
    'Direito de Família':    'purple',
    'Direito Bancário':      'success',
    'Previdência Social':    'info',
    'Indefinida':            'secondary',
}


# ── Filtro Jinja2 ─────────────────────────────────────────────────────────────

@app.template_filter('urlencode')
def _urlencode_filter(s):
    return quote_plus(str(s))


# ── Auth ──────────────────────────────────────────────────────────────────────

def requer_login(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('logado'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


# ── Funções de controle de histórico ─────────────────────────────────────────

def registrar_pergunta(numero, area):
    hoje = str(date.today())
    if numero not in historico:
        historico[numero] = {}
    if hoje not in historico[numero]:
        historico[numero][hoje] = {}
    if area not in historico[numero][hoje]:
        historico[numero][hoje][area] = 0
    historico[numero][hoje][area] += 1
    return historico[numero][hoje][area]


def total_perguntas_hoje(numero):
    hoje = str(date.today())
    if numero not in historico or hoje not in historico[numero]:
        return 0
    return sum(historico[numero][hoje].values())


# ── Processamento do consentimento ────────────────────────────────────────────

def processar_consentimento(mensagem, numero, sessao):
    escolha    = mensagem.strip()
    nome_wa    = sessao.get('nome_whatsapp', '')
    nome_txt   = f", *{nome_wa}*" if nome_wa else ""

    if escolha == "1":
        registrar_consentimento(numero)
        _del_sessao(numero)
        return (
            f"✅ Consentimento registrado. Obrigado{nome_txt}!\n\n"
            "Agora pode me descrever sua situação jurídica. "
            "Estou aqui para orientar você."
        )

    elif escolha == "2":
        revogar_consentimento(numero)
        _del_sessao(numero)
        return (
            "Tudo bem. Seus dados não serão utilizados.\n\n"
            "Se mudar de ideia no futuro, é só me enviar uma mensagem "
            "e apresentarei o termo novamente."
        )

    else:
        return (
            "Não entendi sua resposta.\n\n"
            "Por favor, responda apenas com:\n\n"
            "1️⃣ Sim, concordo — quero continuar\n"
            "2️⃣ Não concordo — quero sair"
        )


# ── Webhook WhatsApp (Evolution API) ─────────────────────────────────────────

@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    dados = request.get_json(silent=True) or {}

    # Evolution API envia o evento dentro de dados["data"]["message"]
    evento = dados.get("data", {})
    chave  = evento.get("key", {})

    # Ignorar mensagens enviadas pelo próprio bot
    if chave.get("fromMe"):
        return '', 200

    numero_raw = chave.get("remoteJid", "")   # ex: 5519...@s.whatsapp.net
    numero_db  = _normalizar_numero(numero_raw)  # apenas dígitos para o BD
    nome_wa = evento.get("pushName", "").strip()

    # Extrair texto da mensagem (texto simples ou estendido)
    msg_obj  = evento.get("message", {})
    mensagem = (
        msg_obj.get("conversation")
        or msg_obj.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    # Mensagem de áudio: baixar, transcrever, registrar e avisar o usuário
    if not mensagem and "audioMessage" in msg_obj:
        _, caminho_rel = _baixar_audio_evo(msg_obj, numero_raw)
        transcricao = _transcrever_audio(
            os.path.join(_AUDIO_DIR, caminho_rel)
        ) if caminho_rel else None

        aviso = (
            "Recebi seu áudio! 🎧\n\n"
            "Para melhor atendimento, por favor escreva sua situação jurídica em texto também. 📝\n\n"
            + (f"_Transcrição detectada: \"{transcricao}\"_" if transcricao else
               "_Não consegui transcrever automaticamente._")
        )
        _enviar_mensagem(numero_raw, aviso)
        registrar_mensagem(numero_db, 'entrada', '[áudio]',
                           audio_path=caminho_rel, transcricao=transcricao)
        return '', 200

    # Ignorar eventos sem texto (stickers, figurinhas, etc.)
    if not mensagem:
        return '', 200

    sessao = _get_sessao(numero_db)
    estado = sessao.get("estado", "novo")

    # Atualiza nome do WhatsApp na sessão se disponível
    if nome_wa and sessao.get('nome_whatsapp') != nome_wa:
        sessao['nome_whatsapp'] = nome_wa
        if estado != "novo":
            _set_sessao(numero_db, sessao)

    # Comando REINICIAR — só disponível em MODO_TESTE
    if MODO_TESTE and mensagem.strip().upper() == "REINICIAR":
        _del_sessao(numero_db)
        revogar_consentimento(numero_db)
        if numero_db in historico:
            del historico[numero_db]
        _enviar_mensagem(numero_raw, "🔄 Sessão reiniciada. Pode começar uma nova conversa!")
        return '', 200

    # Cancelar/Sair reseta a sessão em qualquer estado
    _CANCELAR = {"cancelar", "sair", "cancel", "parar", "pare", "encerrar", "encerramento", "voltar"}
    if mensagem.strip().lower() in _CANCELAR:
        _del_sessao(numero_db)
        _enviar_mensagem(
            numero_raw,
            "Tudo bem! Sua sessão foi encerrada.\n\n"
            "Quando quiser, é só me enviar uma nova mensagem descrevendo sua situação jurídica. 😊"
        )
        registrar_mensagem(numero_db, 'entrada', mensagem)
        registrar_mensagem(numero_db, 'saida', "Sessão encerrada pelo usuário.")
        return '', 200

    if estado == "aguardando_consentimento":
        resposta = processar_consentimento(mensagem, numero_db, sessao)
    elif estado == "aguardando_esclarecimento":
        resposta = processar_esclarecimento(mensagem, numero_db, sessao)
    elif estado == "fazendo_perguntas":
        resposta = processar_resposta_pergunta(mensagem, numero_db, sessao)
    elif estado == "aguardando_escolha":
        resposta = processar_escolha(mensagem, numero_db, sessao)
    elif verificar_consentimento(numero_db):
        resposta = processar_relato(mensagem, numero_db)
    else:
        sessao_nova = {"estado": "aguardando_consentimento"}
        if nome_wa:
            sessao_nova['nome_whatsapp'] = nome_wa
        _set_sessao(numero_db, sessao_nova)
        resposta = _montar_termo(nome_wa)

    registrar_mensagem(numero_db, 'entrada', mensagem)
    registrar_mensagem(numero_db, 'saida', resposta)
    _enviar_mensagem(numero_raw, resposta)
    return '', 200


# ── Processamento do relato ───────────────────────────────────────────────────

_SAUDACOES_RELATO = {
    "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite",
    "hey", "hi", "hello", "tudo bem", "tudo bom", "oi tudo bem",
    "ola tudo bem", "oi boa tarde", "oi bom dia", "oi boa noite"
}

_AGRADECIMENTOS = {
    "obrigada", "obrigado", "obg", "obgda", "valeu", "muito obrigada",
    "muito obrigado", "grata", "grato", "agradeço", "agradeco",
    "obrigada!", "obrigado!", "valeu!", "muito obg", "mt obrigada",
    "mt obrigado", "thanks", "thank you"
}

def processar_relato(mensagem, numero):
    msg = mensagem.strip().lower()

    if msg in _SAUDACOES_RELATO:
        return (
            "Olá! 👋 Sou o assistente jurídico do ACESSUS Direito Popular.\n\n"
            "Estou aqui para ajudar você a entender seus direitos e orientar sobre sua situação jurídica.\n\n"
            "Por favor, me descreva brevemente o que está acontecendo — "
            "pode escrever com suas próprias palavras, sem preocupação com termos jurídicos."
        )

    if msg in _AGRADECIMENTOS or any(ag in msg for ag in _AGRADECIMENTOS):
        return (
            "Fico feliz em ter ajudado! 😊\n\n"
            "Se precisar de mais orientações no futuro, é só me enviar uma mensagem descrevendo sua situação.\n\n"
            "O ACESSUS Direito Popular está sempre à disposição! 🤝"
        )

    total = total_perguntas_hoje(numero)
    if not MODO_TESTE and total >= LIMITE_BLOQUEIO:
        _set_sessao(numero, {
            "estado": "aguardando_escolha",
            "protocolo": "",
            "area": "",
            "sub_area": "",
            "opcoes": ["advogado", "defensoria"],
            "respostas": {}
        })
        return (
            "Identifiquei que você já realizou várias consultas hoje por "
            "esta via.\n\n"
            "Para garantir que seu caso receba a atenção adequada, "
            "não consigo fornecer mais orientações por mensagem.\n\n"
            "Por favor, escolha uma das opções de atendimento humano:\n\n"
            "1️⃣ Encaminhar para advogado parceiro\n"
            "2️⃣ Informações da Defensoria Pública\n\n"
            "_Responda com 1 ou 2._"
        )

    resultado  = motor.analisar(mensagem)
    area       = resultado.get("area", "Indefinida")
    sub_area   = resultado.get("sub_area", "indefinida")
    prioridade = resultado.get("prioridade", 3)

    # Área não identificada → pergunta o tema antes de mostrar opções genéricas
    if area == "Indefinida":
        sessao_atual = _get_sessao(numero)
        _set_sessao(numero, {
            "estado": "aguardando_esclarecimento",
            "relato_original": mensagem,
            "prioridade": prioridade,
            "nome_whatsapp": sessao_atual.get('nome_whatsapp', '')
        })
        return (
            "Recebi seu relato! Para te orientar corretamente, "
            "preciso entender melhor o tema.\n\n"
            "Sua situação é sobre qual dessas áreas?\n\n"
            "1️⃣ Banco ou finanças (conta, cartão, empréstimo, PIX)\n"
            "2️⃣ Trabalho (demissão, salário, FGTS)\n"
            "3️⃣ Compra ou serviço (produto, loja, internet)\n"
            "4️⃣ Família (pensão, guarda, divórcio)\n"
            "5️⃣ INSS ou previdência\n"
            "6️⃣ Outro assunto\n\n"
            "_Responda com o número correspondente._"
        )

    vezes = registrar_pergunta(numero, area)

    # 2ª pergunta sobre o mesmo tema — resposta reduzida (desativado em MODO_TESTE)
    if not MODO_TESTE and vezes == LIMITE_AVISO:
        protocolo = gerar_id_sequencial()
        salvar_caso(
            protocolo=protocolo,
            descricao=mensagem,
            classificacao=area,
            prioridade=f"Prioridade {prioridade}",
            acao_sugerida="Repetição de consulta",
            whatsapp=numero
        )
        opcoes_texto, opcoes_lista = obter_opcoes(area, sub_area, {})
        _set_sessao(numero, {
            "estado": "aguardando_escolha",
            "protocolo": protocolo,
            "area": area,
            "sub_area": sub_area,
            "opcoes": opcoes_lista,
            "respostas": {}
        })
        return (
            f"*Protocolo:* {protocolo}\n\n"
            f"Já orientei sobre *{area}* anteriormente nesta conversa.\n\n"
            "Posso confirmar que a legislação prevê os direitos que já "
            "informei, mas uma análise específica exige atendimento com "
            "um profissional habilitado.\n\n"
            + opcoes_texto
            + DISCLAIMER
        )

    return iniciar_questionario(area, sub_area, mensagem, numero, prioridade)


# ── Esclarecimento de área (quando não identificada automaticamente) ──────────

_MAPA_ESCLARECIMENTO = {
    "1": ("Direito Bancário",      "bancario",        2),
    "2": ("Direito Trabalhista",   "trabalhista",     2),
    "3": ("Direito do Consumidor", "consumidor_geral", 3),
    "4": ("Direito de Família",    "familia",         2),
    "5": ("Previdência Social",    "inss",            2),
}

def processar_esclarecimento(mensagem, numero, sessao):
    escolha = mensagem.strip()
    relato  = sessao.get("relato_original", mensagem)

    if escolha in _MAPA_ESCLARECIMENTO:
        area, sub_area, prioridade = _MAPA_ESCLARECIMENTO[escolha]
        # Salva frase original como sugestão de keyword para revisão no painel
        if len(relato.strip()) >= 5:
            try:
                registrar_sugestao(relato.strip(), area, sub_area)
            except Exception:
                pass
        registrar_pergunta(numero, area)
        return iniciar_questionario(area, sub_area, relato, numero, prioridade)

    # Opção 6 ou resposta não reconhecida → opções genéricas
    _set_sessao(numero, {
        "estado": "aguardando_escolha",
        "protocolo": "",
        "area": "Indefinida",
        "sub_area": "indefinida",
        "opcoes": ["advogado", "procon", "cejusc", "jec"],
        "respostas": {},
        "nome_whatsapp": sessao.get('nome_whatsapp', '')
    })
    return _opcoes_indefinida()


# ── Questionário ──────────────────────────────────────────────────────────────

def iniciar_questionario(area, sub_area, relato, numero, prioridade):
    perguntas_area = obter_perguntas(area, sub_area)

    # Sempre pergunta o nome completo primeiro
    pergunta_nome = {
        "chave": "nome_completo",
        "texto": "Para registrar seu caso, preciso do seu *nome completo*."
    }
    perguntas = [pergunta_nome] + perguntas_area

    sessao_atual = _get_sessao(numero)
    sessao_nova = {
        "estado": "fazendo_perguntas",
        "area": area,
        "sub_area": sub_area,
        "relato_original": relato,
        "perguntas": perguntas,
        "indice_atual": 0,
        "respostas": {},
        "prioridade": prioridade,
        "nome_whatsapp": sessao_atual.get('nome_whatsapp', '')
    }
    _set_sessao(numero, sessao_nova)

    if not perguntas:
        return finalizar_questionario(numero, sessao_nova)

    return (
        f"Entendo, seu caso envolve *{area}*.\n\n"
        "Para te orientar da melhor forma, preciso entender um pouco "
        "mais sobre o que aconteceu.\n\n"
        f"{perguntas[0]['texto']}"
    )


def processar_resposta_pergunta(mensagem, numero, sessao):
    perguntas = sessao["perguntas"]
    indice    = sessao["indice_atual"]
    respostas = sessao["respostas"]

    if indice >= len(perguntas):
        _del_sessao(numero)
        return (
            "Houve uma atualização no sistema e sua sessão anterior ficou desatualizada.\n\n"
            "Por favor, descreva novamente sua situação jurídica para eu te orientar."
        )

    pergunta_atual = perguntas[indice]
    chave          = pergunta_atual["chave"]
    especial       = pergunta_atual.get("especial")

    _SAUDACOES = {"olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", "hey", "hi", "hello"}
    resposta_limpa = mensagem.strip()

    if chave == "cidade" and resposta_limpa.lower() in _SAUDACOES:
        _set_sessao(numero, sessao)
        return "Por favor, me informe o nome da sua cidade para continuar."

    # Converte número da opção para o texto legível (ex: "2" → "Não")
    opcoes = pergunta_atual.get("opcoes", {})
    respostas[chave] = opcoes.get(resposta_limpa, resposta_limpa)

    if especial == "risco_vida":
        r = mensagem.strip().lower()
        if r in ("1", "sim", "s") or "sim" in r or "urgência" in r or "urgencia" in r:
            sessao["respostas"] = respostas
            return finalizar_questionario(numero, sessao, urgente=True)

    elif especial == "foi_inss":
        r = mensagem.strip().lower()
        if r in ("2", "não", "nao", "n") or ("não" in r and "já" not in r) or ("nao" in r and "ja" not in r) or "ainda" in r:
            sessao["respostas"] = respostas
            return finalizar_questionario(numero, sessao)

    proximo = indice + 1

    if proximo >= len(perguntas):
        sessao["respostas"] = respostas
        return finalizar_questionario(numero, sessao)

    sessao["indice_atual"] = proximo
    sessao["respostas"]    = respostas
    _set_sessao(numero, sessao)

    return perguntas[proximo]["texto"]


def finalizar_questionario(numero, sessao, urgente=False):
    area       = sessao["area"]
    sub_area   = sessao["sub_area"]
    relato     = sessao.get("relato_original", "")
    respostas  = sessao.get("respostas", {})
    prioridade = sessao.get("prioridade", 3)

    protocolo     = gerar_id_sequencial()
    nome_completo = respostas.get('nome_completo', sessao.get('nome_whatsapp', 'Via WhatsApp'))
    resumo_db     = _gerar_resumo_db(relato, area, sub_area, respostas)

    salvar_caso(
        protocolo=protocolo,
        descricao=resumo_db,
        classificacao=area,
        prioridade=f"Prioridade {prioridade}",
        acao_sugerida="",
        whatsapp=numero,
        nome_cliente=nome_completo
    )

    if urgente:
        opcoes_texto = (
            "⚠️ *Situação de urgência identificada.*\n\n"
            "Neste caso, o ideal é ser atendido por um advogado o mais rápido possível.\n\n"
            "1️⃣ Encaminhar para advogado parceiro agora\n\n"
            "_Responda com 1._"
        )
        opcoes_lista = ["advogado_urgente"]
    else:
        opcoes_texto, opcoes_lista = obter_opcoes(area, sub_area, respostas)

    _set_sessao(numero, {
        "estado": "aguardando_escolha",
        "protocolo": protocolo,
        "area": area,
        "sub_area": sub_area,
        "opcoes": opcoes_lista,
        "respostas": respostas
    })

    return (
        f"Obrigado pelas informações.\n\n"
        f"*Protocolo:* {protocolo}\n\n"
        f"{opcoes_texto}"
        + DISCLAIMER
    )


def _gerar_resumo_db(relato, area, sub_area, respostas):
    linhas = [
        f"RELATO: {relato}",
        f"ÁREA: {area} / {sub_area}",
        "---"
    ]
    for chave, valor in respostas.items():
        linhas.append(f"{chave.upper().replace('_', ' ')}: {valor}")
    return "\n".join(linhas)


# ── Opções por área ───────────────────────────────────────────────────────────

def obter_opcoes(area, sub_area, respostas):
    """Retorna (texto_das_opcoes, lista_de_chaves_de_opcao)."""

    if area == "Direito do Consumidor" and sub_area == "plano_saude":
        risco = respostas.get("risco_vida", "2").strip().lower()
        if risco in ("1", "sim", "s") or "sim" in risco:
            return (
                "⚠️ *Situação de urgência identificada.*\n\n"
                "1️⃣ Encaminhar para advogado parceiro agora\n\n"
                "_Responda com 1._",
                ["advogado_urgente"]
            )
        return (
            "De acordo com o que você me disse, essas são suas opções:\n\n"
            "1️⃣ Encaminhar para advogado parceiro\n"
            "2️⃣ Registrar reclamação na ANS\n"
            "3️⃣ Não preciso de atendimento agora\n\n"
            "_Responda com 1, 2 ou 3._",
            ["advogado", "ans", "sem_atendimento"]
        )

    if area == "Direito Trabalhista":
        return (
            "De acordo com o que você me disse, você pode ter seus direitos "
            "resguardados por uma ação judicial.\n\n"
            "1️⃣ Encaminhar para advogado parceiro\n"
            "2️⃣ Não preciso de atendimento agora\n\n"
            "_Responda com 1 ou 2._",
            ["advogado", "sem_atendimento"]
        )

    if area == "Direito de Família":
        return (
            "De acordo com o que você me disse, essas são suas opções:\n\n"
            "1️⃣ Encaminhar para advogado parceiro\n"
            "2️⃣ Informações da Defensoria Pública\n"
            "3️⃣ Não preciso de atendimento agora\n\n"
            "_Responda com 1, 2 ou 3._",
            ["advogado", "defensoria", "sem_atendimento"]
        )

    if area == "Previdência Social":
        foi = respostas.get("foi_ao_inss", "2").strip().lower()
        if foi in ("1", "sim", "s") or "sim" in foi or "já" in foi or "ja " in foi:
            return (
                "De acordo com o que você me disse, essas são suas opções:\n\n"
                "1️⃣ Encaminhar para advogado parceiro\n"
                "2️⃣ Não preciso de atendimento agora\n\n"
                "_Responda com 1 ou 2._",
                ["advogado", "sem_atendimento"]
            )
        return (
            "De acordo com o que você me disse, essas são suas opções:\n\n"
            "1️⃣ Encaminhar para advogado parceiro\n"
            "2️⃣ Acessar o Meu INSS\n"
            "3️⃣ Não preciso de atendimento agora\n\n"
            "_Responda com 1, 2 ou 3._",
            ["advogado", "meu_inss", "sem_atendimento"]
        )

    if area == "Direito Bancário":
        return (
            "De acordo com o que você me disse, essas são suas opções:\n\n"
            "1️⃣ Encaminhar para advogado parceiro\n"
            "2️⃣ Registrar reclamação no Banco Central\n"
            "3️⃣ Informações do CEJUSC\n"
            "4️⃣ Não preciso de atendimento agora\n\n"
            "_Responda com 1, 2, 3 ou 4._",
            ["advogado", "banco_central", "cejusc", "sem_atendimento"]
        )

    if area == "Indefinida":
        return _opcoes_indefinida(), ["advogado", "procon", "cejusc", "jec"]

    cidade = respostas.get("cidade", "").strip()
    procon_label = f"Informações do Procon de {cidade.title()}" if cidade else "Informações do Procon"
    return (
        "De acordo com o que você me disse, você pode ter seus direitos "
        "resguardados por uma ação administrativa ou judicial.\n\n"
        "1️⃣ Encaminhar para advogado parceiro\n"
        "2️⃣ Informações da Defensoria Pública\n"
        "3️⃣ Informações do CEJUSC\n"
        f"4️⃣ {procon_label}\n"
        "5️⃣ Não preciso de atendimento agora\n\n"
        "_Responda com 1, 2, 3, 4 ou 5._",
        ["advogado", "defensoria", "cejusc", "procon", "sem_atendimento"]
    )


def _opcoes_indefinida():
    return (
        "De acordo com o que você me disse, essas são suas opções:\n\n"
        "1️⃣ Encaminhar para advogado parceiro\n"
        "2️⃣ Informações do Procon\n"
        "3️⃣ Informações do CEJUSC\n"
        "4️⃣ Informações do Juizado Especial Cível\n\n"
        "_Responda com 1, 2, 3 ou 4._"
    )


# ── Processamento da escolha ──────────────────────────────────────────────────

def processar_escolha(mensagem, numero, sessao):
    protocolo = sessao.get("protocolo", "")
    area      = sessao.get("area", "")
    opcoes    = sessao.get("opcoes", [])
    respostas = sessao.get("respostas", {})
    escolha   = mensagem.strip()

    try:
        indice = int(escolha) - 1
        if indice < 0 or indice >= len(opcoes):
            raise ValueError
        opcao = opcoes[indice]
    except (ValueError, IndexError):
        _set_sessao(numero, sessao)
        numeros = " ou ".join(str(i) for i in range(1, len(opcoes) + 1))
        return f"Não entendi sua resposta. Por favor, responda com {numeros}."

    _del_sessao(numero)

    cidade        = respostas.get("cidade", "").strip()
    protocolo_txt = f"\n\n*Protocolo do seu caso:* {protocolo}" if protocolo else ""

    if opcao in ("advogado", "advogado_urgente"):
        urgente  = (opcao == "advogado_urgente")
        prefixo  = "⚠️ *Caso urgente encaminhado.*\n\n" if urgente else "✅ *Caso encaminhado para advogado parceiro.*\n\n"
        area_txt = f"*Área:* {area}\n\n" if area else ""
        prot_txt = f"*Protocolo:* {protocolo}\n\n" if protocolo else ""

        # Notifica advogado por e-mail (roteia pelo banco; fallback para env var)
        if protocolo:
            from banco.banco_dados import buscar_caso_por_id
            from ia.notificacoes import enviar_email_advogado
            dados = buscar_caso_por_id(protocolo)
            if dados:
                wa_cliente = dados[3]
                relato_db  = dados[4]
                tipo_db    = dados[5]
                prio_db    = dados[6]
                adv = buscar_advogado_por_area(tipo_db or area)
                enviar_email_advogado(
                    protocolo=protocolo,
                    area=tipo_db or area,
                    prioridade=prio_db or "Prioridade 3",
                    whatsapp_cliente=wa_cliente,
                    relato=relato_db,
                    urgente=urgente,
                    email_destino=adv['email'] if adv else None
                )

        return (
            prefixo + prot_txt + area_txt +
            "Um advogado receberá seu caso e entrará em contato em breve.\n\n"
            "Guarde seu protocolo para acompanhamento."
            + DISCLAIMER
        )

    if opcao == "defensoria":
        return f"✅ *Informações da Defensoria Pública:*\n\n{DEFENSORIA_CAMPINAS}" + protocolo_txt + DISCLAIMER

    if opcao == "cejusc":
        return f"✅ *Informações do CEJUSC:*\n\n{CEJUSC_INFO}" + protocolo_txt + DISCLAIMER

    if opcao == "procon":
        procon_cidade = f" de {cidade.title()}" if cidade else ""
        return f"✅ *Informações do Procon{procon_cidade}:*\n\n{PROCON_INFO}" + protocolo_txt + DISCLAIMER

    if opcao == "ans":
        return f"✅ *Como registrar reclamação na ANS:*\n\n{ANS_INFO}" + protocolo_txt + DISCLAIMER

    if opcao == "banco_central":
        return f"✅ *Como registrar reclamação no Banco Central:*\n\n{BC_INFO}" + protocolo_txt + DISCLAIMER

    if opcao == "meu_inss":
        return f"✅ *Acesse o Meu INSS:*\n\n{MEU_INSS_INFO}" + protocolo_txt + DISCLAIMER

    if opcao == "jec":
        return f"✅ *Informações do Juizado Especial Cível:*\n\n{JEC_INFO}" + protocolo_txt + DISCLAIMER

    if opcao == "sem_atendimento":
        prot_msg = f" com o protocolo *{protocolo}*" if protocolo else ""
        return (
            f"Tudo bem! Seu caso foi registrado{prot_msg}.\n\n"
            "Se precisar de ajuda no futuro, é só me enviar uma mensagem."
            + DISCLAIMER
        )

    return "Opção não reconhecida. Por favor, tente novamente." + DISCLAIMER


# ── Painel do Advogado ────────────────────────────────────────────────────────

def _extrair_resumo(relato, max_chars=220):
    if not relato:
        return ''
    if 'RELATO:' in relato:
        for linha in relato.split('\n'):
            if linha.strip().startswith('RELATO:'):
                return linha.replace('RELATO:', '').strip()[:max_chars]
    return relato[:max_chars]


def _formatar_data_web(data_cadastro):
    try:
        return datetime.fromisoformat(str(data_cadastro)[:19]).strftime('%d/%m/%Y %H:%M')
    except Exception:
        return str(data_cadastro)[:16]


@app.route('/advogados/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        if request.form.get('senha', '').strip() == ADVOGADOS_SENHA.strip():
            session['logado'] = True
            return redirect(url_for('dashboard'))
        erro = 'Senha incorreta.'
    return render_template('login.html', erro=erro)


@app.route('/advogados/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/advogados')
@requer_login
def dashboard():
    from banco.banco_dados import listar_casos

    area_filtro = request.args.get('area', '')
    prio_filtro = request.args.get('prioridade', '')

    todos = listar_casos()
    areas = sorted({c[5] for c in todos if c[5]})

    casos = []
    for c in todos:
        id_caso, nome, email, whatsapp, relato, tipo, prio, anexos, data_cad = c
        if area_filtro and tipo != area_filtro:
            continue
        if prio_filtro and prio != prio_filtro:
            continue
        casos.append({
            'id':         id_caso,
            'whatsapp':   whatsapp or '',
            'tipo':       tipo or 'Indefinida',
            'prioridade': prio or '—',
            'data_fmt':   _formatar_data_web(data_cad),
            'resumo':     _extrair_resumo(relato),
            'cor':        _COR_AREA.get(tipo, 'secondary'),
        })

    return render_template('dashboard.html',
                           casos=casos,
                           areas=areas,
                           area_filtro=area_filtro,
                           prio_filtro=prio_filtro)


def _montar_caso_dict(dados):
    """Converte tupla do BD em dicionário para templates."""
    id_caso, nome, email, whatsapp, relato, tipo, prio, anexos, data_cad, notas, link_video = dados
    campos = []
    if relato and 'RELATO:' in relato:
        for linha in relato.split('\n'):
            linha = linha.strip()
            if not linha or linha == '---':
                continue
            if ':' in linha:
                chave, _, valor = linha.partition(':')
                campos.append((chave.strip().title().replace('_', ' '), valor.strip()))
    else:
        campos = [('Relato', relato or '')]
    return {
        'id':         id_caso,
        'nome':       nome or '—',
        'email':      email or '',
        'whatsapp':   whatsapp or '',
        'tipo':       tipo or 'Indefinida',
        'prioridade': prio or '—',
        'data_fmt':   _formatar_data_web(data_cad),
        'campos':     campos,
        'relato_raw': relato or '',
        'anexos':     [a.strip() for a in (anexos or '').split(',') if a.strip()],
        'notas':      notas or '',
        'link_video': link_video or '',
        'cor':        _COR_AREA.get(tipo, 'secondary'),
    }


@app.route('/advogados/caso/<caso_id>')
@requer_login
def ver_caso(caso_id):
    dados = buscar_caso_por_id(caso_id)
    if not dados:
        return 'Caso não encontrado.', 404
    return render_template('caso.html', caso=_montar_caso_dict(dados),
                           areas=AREAS_JURIDICAS)


@app.route('/advogados/caso/<caso_id>/editar', methods=['POST'])
@requer_login
def editar_caso(caso_id):
    atualizar_caso(
        caso_id,
        nome_cliente=request.form.get('nome_cliente') or None,
        tipo_caso=request.form.get('tipo_caso') or None,
        prioridade=request.form.get('prioridade') or None,
        notas=request.form.get('notas'),
        link_video=request.form.get('link_video') or None,
    )
    return redirect(f'/advogados/caso/{caso_id}')


@app.route('/advogados/caso/<caso_id>/deletar', methods=['POST'])
@requer_login
def deletar_caso_route(caso_id):
    deletar_caso(caso_id)
    return redirect('/advogados')


@app.route('/advogados/caso/<caso_id>/upload', methods=['POST'])
@requer_login
def upload_caso(caso_id):
    arquivo = request.files.get('arquivo')
    if not arquivo or not arquivo.filename:
        return redirect(f'/advogados/caso/{caso_id}')
    if not _extensao_permitida(arquivo.filename):
        return redirect(f'/advogados/caso/{caso_id}')
    pasta = os.path.join(_UPLOAD_DIR, 'casos', caso_id)
    os.makedirs(pasta, exist_ok=True)
    nome_seguro = secure_filename(arquivo.filename)
    arquivo.save(os.path.join(pasta, nome_seguro))
    adicionar_upload_caso(caso_id, nome_seguro)
    return redirect(f'/advogados/caso/{caso_id}')


@app.route('/advogados/uploads/<caso_id>/<filename>')
@requer_login
def servir_upload(caso_id, filename):
    pasta = os.path.join(_UPLOAD_DIR, 'casos', caso_id)
    return send_from_directory(pasta, filename)


@app.route('/advogados/audio/<path:caminho>')
@requer_login
def servir_audio(caminho):
    return send_from_directory(_AUDIO_DIR, caminho)


@app.route('/advogados/pdf/<caso_id>')
@requer_login
def baixar_pdf(caso_id):
    from relatorios.gerador_pdf import gerar_pdf_caso

    dados = buscar_caso_por_id(caso_id)
    if not dados:
        return 'Caso não encontrado.', 404

    # gerador_pdf espera 9 colunas (sem notas); passa apenas as primeiras 9
    caminho = gerar_pdf_caso(dados[:9])
    return send_file(
        caminho,
        as_attachment=True,
        download_name=f'caso_{caso_id}.pdf',
        mimetype='application/pdf'
    )


# ── Gestão de advogados ───────────────────────────────────────────────────────

@app.route('/advogados/novo-caso', methods=['GET', 'POST'])
@requer_login
def novo_caso_manual():
    from banco.banco_dados import inserir_caso
    erro = None
    if request.method == 'POST':
        nome      = request.form.get('nome', '').strip()
        whatsapp  = request.form.get('whatsapp', '').strip()
        area      = request.form.get('area', '').strip()
        prioridade = request.form.get('prioridade', '3').strip()
        relato    = request.form.get('relato', '').strip()

        if not nome or not relato or not area:
            erro = 'Nome, área jurídica e relato são obrigatórios.'
        else:
            protocolo = gerar_id_sequencial()
            inserir_caso(
                id_caso=protocolo,
                nome_cliente=nome,
                email='',
                whatsapp=whatsapp,
                relato=relato,
                tipo_caso=area,
                prioridade=f'Prioridade {prioridade}',
                anexos='',
                encaminhamento='Cadastro manual'
            )
            return redirect(url_for('dashboard'))

    return render_template('novo_caso.html',
                           areas_juridicas=AREAS_JURIDICAS,
                           erro=erro)


@app.route('/advogados/lista')
@requer_login
def lista_advogados():
    advs = listar_advogados()
    return render_template('advogados_lista.html', advogados=advs)


@app.route('/advogados/cadastrar', methods=['GET', 'POST'])
@requer_login
def cadastrar_advogado():
    erro = None
    if request.method == 'POST':
        nome      = request.form.get('nome', '').strip()
        email     = request.form.get('email', '').strip()
        whatsapp  = request.form.get('whatsapp', '').strip()
        oab_num   = request.form.get('oab_numero', '').strip()
        oab_uf    = request.form.get('oab_uf', '').strip()
        areas     = request.form.getlist('areas')

        if not nome or not email:
            erro = 'Nome e e-mail são obrigatórios.'
        else:
            criar_advogado(nome, email, whatsapp, oab_num, oab_uf, areas)
            return redirect(url_for('lista_advogados'))

    return render_template('advogados_cadastrar.html',
                           areas_juridicas=AREAS_JURIDICAS,
                           uf_lista=UF_LISTA,
                           erro=erro)


@app.route('/advogados/<int:adv_id>/status', methods=['POST'])
@requer_login
def toggle_advogado(adv_id):
    ativo_str = request.form.get('ativo', '0')
    atualizar_status_advogado(adv_id, ativo_str == '1')
    return redirect(url_for('lista_advogados'))


# ── Monitoramento de conversas ────────────────────────────────────────────────

@app.route('/advogados/conversas')
@requer_login
def conversas_lista():
    contatos = listar_conversas()
    for c in contatos:
        c['ultima_fmt'] = _formatar_data_web(c['ultima'])
        c['numero_limpo'] = c['whatsapp'].replace('whatsapp:', '')
    return render_template('conversas_lista.html', contatos=contatos)


@app.route('/advogados/conversas/<path:numero>')
@requer_login
def conversa_detalhe(numero):
    # Tenta com o número como está (novo formato: só dígitos)
    mensagens = buscar_conversa_por_numero(numero)
    if not mensagens:
        # Compatibilidade com formato antigo Twilio (whatsapp:+551999...)
        mensagens = buscar_conversa_por_numero(f'whatsapp:{numero}')
    for m in mensagens:
        m['data_fmt'] = _formatar_data_web(m['data_hora'])
    return render_template('conversa_detalhe.html',
                           mensagens=mensagens,
                           numero=numero)


# ── Sugestões de keywords ─────────────────────────────────────────────────────

@app.route('/advogados/sugestoes')
@requer_login
def sugestoes_lista():
    pendentes = listar_sugestoes_pendentes()
    aprovadas = listar_keywords_aprovadas()
    for s in pendentes:
        s['data_fmt'] = _formatar_data_web(s['data_hora'])
    return render_template('sugestoes.html', pendentes=pendentes, aprovadas=aprovadas)


@app.route('/advogados/sugestoes/aprovar/<int:sugestao_id>', methods=['POST'])
@requer_login
def sugestoes_aprovar(sugestao_id):
    aprovar_sugestao(sugestao_id)
    motor.recarregar_extras()
    return redirect('/advogados/sugestoes')


@app.route('/advogados/sugestoes/ignorar/<int:sugestao_id>', methods=['POST'])
@requer_login
def sugestoes_ignorar(sugestao_id):
    ignorar_sugestao(sugestao_id)
    return redirect('/advogados/sugestoes')


# ── Rota de verificação ───────────────────────────────────────────────────────

@app.route("/", methods=['GET'])
def home():
    return "Agente de Triagem Jurídica Online - Sistema Ativo", 200


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
