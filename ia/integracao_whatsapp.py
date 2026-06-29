import os
from datetime import date, datetime
from functools import wraps
from urllib.parse import quote_plus
from flask import (Flask, request, session, redirect,
                   url_for, render_template, send_file)
from twilio.twiml.messaging_response import MessagingResponse
from ia.motor_decisao import MotorDecisaoJuridica as MotorDecisao
from ia.base_conhecimento import (
    obter_perguntas, CEJUSC_INFO, PROCON_INFO, JEC_INFO, ANS_INFO, MEU_INSS_INFO
)
from banco.banco_dados import (salvar_caso, criar_banco, gerar_id_sequencial,
                               registrar_consentimento, verificar_consentimento,
                               revogar_consentimento, salvar_sessao, obter_sessao,
                               deletar_sessao, criar_advogado, listar_advogados,
                               buscar_advogado_por_area, atualizar_status_advogado)

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

# ── Sessões e consentimentos persistidos no banco ────────────────────────────
# Substituem os dicts/sets em memória — sobrevivem a reinícios do servidor.

def _get_sessao(numero):
    dados = obter_sessao(numero)
    if dados and 'area' in dados and 'sub_area' in dados:
        dados['perguntas'] = obter_perguntas(dados['area'], dados['sub_area'])
    return dados or {}

def _set_sessao(numero, dados):
    salvar_sessao(numero, dados)

def _del_sessao(numero):
    deletar_sessao(numero)

# ── Histórico diário ────────────────────────────────────────────────────────
# historico[numero][data][area] = quantidade de perguntas
historico = {}

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


# ── Webhook WhatsApp ──────────────────────────────────────────────────────────

@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    mensagem   = request.values.get('Body', '').strip()
    numero     = request.values.get('From', '')
    nome_wa    = request.values.get('ProfileName', '').strip()

    resp   = MessagingResponse()
    sessao = _get_sessao(numero)
    estado = sessao.get("estado", "novo")

    # Atualiza nome do WhatsApp na sessão se disponível
    if nome_wa and sessao.get('nome_whatsapp') != nome_wa:
        sessao['nome_whatsapp'] = nome_wa
        if estado != "novo":
            _set_sessao(numero, sessao)

    if estado == "aguardando_consentimento":
        resposta = processar_consentimento(mensagem, numero, sessao)
    elif estado == "fazendo_perguntas":
        resposta = processar_resposta_pergunta(mensagem, numero, sessao)
    elif estado == "aguardando_escolha":
        resposta = processar_escolha(mensagem, numero, sessao)
    elif verificar_consentimento(numero):
        resposta = processar_relato(mensagem, numero)
    else:
        sessao_nova = {"estado": "aguardando_consentimento"}
        if nome_wa:
            sessao_nova['nome_whatsapp'] = nome_wa
        _set_sessao(numero, sessao_nova)
        resposta = _montar_termo(nome_wa)

    resp.message(resposta)
    return str(resp)


# ── Processamento do relato ───────────────────────────────────────────────────

def processar_relato(mensagem, numero):
    total = total_perguntas_hoje(numero)
    if total >= LIMITE_BLOQUEIO:
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

    vezes = registrar_pergunta(numero, area)

    # 2ª pergunta sobre o mesmo tema — resposta reduzida
    if vezes == LIMITE_AVISO:
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

    if area == "Indefinida":
        return (
            "Recebi seu relato, mas não consegui identificar com clareza "
            "a área jurídica.\n\n"
            + _opcoes_indefinida()
        )

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
                _, _, _, wa_cliente, relato_db, tipo_db, prio_db, _, _ = dados
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


@app.route('/advogados/caso/<caso_id>')
@requer_login
def ver_caso(caso_id):
    from banco.banco_dados import buscar_caso_por_id

    dados = buscar_caso_por_id(caso_id)
    if not dados:
        return 'Caso não encontrado.', 404

    id_caso, nome, email, whatsapp, relato, tipo, prio, anexos, data_cad = dados

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

    caso = {
        'id':         id_caso,
        'nome':       nome or '—',
        'email':      email or '',
        'whatsapp':   whatsapp or '',
        'tipo':       tipo or 'Indefinida',
        'prioridade': prio or '—',
        'data_fmt':   _formatar_data_web(data_cad),
        'campos':     campos,
        'anexos':     [a.strip() for a in (anexos or '').split(',') if a.strip()],
        'cor':        _COR_AREA.get(tipo, 'secondary'),
    }

    return render_template('caso.html', caso=caso)


@app.route('/advogados/pdf/<caso_id>')
@requer_login
def baixar_pdf(caso_id):
    from banco.banco_dados import buscar_caso_por_id
    from relatorios.gerador_pdf import gerar_pdf_caso

    dados = buscar_caso_por_id(caso_id)
    if not dados:
        return 'Caso não encontrado.', 404

    caminho = gerar_pdf_caso(dados)
    return send_file(
        caminho,
        as_attachment=True,
        download_name=f'caso_{caso_id}.pdf',
        mimetype='application/pdf'
    )


# ── Gestão de advogados ───────────────────────────────────────────────────────

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


# ── Rota de verificação ───────────────────────────────────────────────────────

@app.route("/", methods=['GET'])
def home():
    return "Agente de Triagem Jurídica Online - Sistema Ativo", 200


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
