import os
from datetime import datetime, date
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from ia.motor_decisao import MotorDecisaoJuridica as MotorDecisao
from ia.base_conhecimento import obter_orientacao_legal
from banco.banco_dados import salvar_caso, criar_banco, gerar_id_sequencial

app = Flask(__name__)
motor = MotorDecisao()
criar_banco()

# ── Memória de sessões ──────────────────────────────────────────────────────
# sessoes[numero] = {
#   "estado": "aguardando_escolha" | "bloqueado",
#   "protocolo": "001_2026",
#   "area": "Direito Trabalhista"
# }
sessoes = {}

# ── Histórico diário ────────────────────────────────────────────────────────
# historico[numero][data][area] = quantidade de perguntas
historico = {}

# ── Constantes ──────────────────────────────────────────────────────────────
LIMITE_AVISO    = 2   # Na 2ª pergunta sobre o mesmo tema → aviso
LIMITE_BLOQUEIO = 3   # Na 3ª pergunta sobre qualquer tema no dia → bloqueia

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


# ── Funções de controle de histórico ────────────────────────────────────────

def registrar_pergunta(numero, area):
    """Registra uma pergunta no histórico diário e retorna quantas vezes
    esse número perguntou sobre essa área hoje."""
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
    """Retorna o total de perguntas feitas pelo número hoje."""
    hoje = str(date.today())
    if numero not in historico or hoje not in historico[numero]:
        return 0
    return sum(historico[numero][hoje].values())


# ── Webhook principal ────────────────────────────────────────────────────────

@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    mensagem = request.values.get('Body', '').strip()
    numero   = request.values.get('From', '')

    resp   = MessagingResponse()
    sessao = sessoes.get(numero, {})
    estado = sessao.get("estado", "novo")

    if estado == "aguardando_escolha":
        resposta = processar_escolha(mensagem, numero, sessao)
    else:
        resposta = processar_relato(mensagem, numero)

    resp.message(resposta)
    return str(resp)


# ── Processamento do relato ──────────────────────────────────────────────────

def processar_relato(mensagem, numero):

    # Verifica bloqueio diário total
    total = total_perguntas_hoje(numero)
    if total >= LIMITE_BLOQUEIO:
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

    # Analisa o relato
    resultado    = motor.analisar(mensagem)
    area         = resultado.get('area', 'Indefinida')
    acao         = resultado.get('acao_sugerida', 'Procure um advogado ou a Defensoria Pública.')
    orientacao   = obter_orientacao_legal(area)
    fundamento   = orientacao.get('fundamento', 'Legislação Civil Geral.')
    explicacao   = orientacao.get('explicacao', 'O caso requer análise detalhada.')

    # Registra e verifica repetição por tema
    vezes = registrar_pergunta(numero, area)

    protocolo = gerar_id_sequencial()
    salvar_caso(
        protocolo=protocolo,
        descricao=mensagem,
        classificacao=area,
        prioridade=f"Prioridade {resultado.get('prioridade', 3)}",
        acao_sugerida=acao
    )

    sessoes[numero] = {
        "estado": "aguardando_escolha",
        "protocolo": protocolo,
        "area": area
    }

    # 2ª pergunta sobre o mesmo tema — resposta reduzida com aviso
    if vezes == LIMITE_AVISO:
        return (
            f"*Protocolo:* {protocolo}\n\n"
            f"Já orientei sobre *{area}* anteriormente nesta conversa.\n\n"
            f"Posso confirmar que a legislação prevê os direitos que já "
            f"informei, mas uma análise específica do seu caso exige "
            f"atendimento com um profissional habilitado.\n\n"
            f"Deseja ser encaminhado?\n\n"
            f"1️⃣ Encaminhar para advogado parceiro\n"
            f"2️⃣ Informações da Defensoria Pública\n"
            f"3️⃣ Não preciso de atendimento agora"
            + DISCLAIMER
        )

    # 1ª pergunta — resposta completa
    if area == "Indefinida":
        return (
            f"*Protocolo:* {protocolo}\n\n"
            "Recebi seu relato, mas não consegui identificar a área "
            "jurídica com clareza.\n\n"
            "Deseja que eu encaminhe seu caso para atendimento?\n\n"
            "1️⃣ Encaminhar para advogado parceiro\n"
            "2️⃣ Informações da Defensoria Pública\n"
            "3️⃣ Não preciso de atendimento agora\n\n"
            "_Responda com o número da opção desejada._"
        )

    return (
        f"*Protocolo:* {protocolo}\n\n"
        f"Seu caso se enquadra em *{area}*.\n\n"
        f"⚖️ *Fundamento legal:* {fundamento}\n\n"
        f"📖 *O que a lei prevê:* {explicacao}\n\n"
        f"💡 *Orientação:* {acao}\n\n"
        f"Deseja encaminhar seu caso?\n\n"
        f"1️⃣ Encaminhar para advogado parceiro\n"
        f"2️⃣ Informações da Defensoria Pública\n"
        f"3️⃣ Não preciso de atendimento agora\n\n"
        f"_Responda com o número da opção desejada._"
        + DISCLAIMER
    )


# ── Processamento da escolha ─────────────────────────────────────────────────

def processar_escolha(mensagem, numero, sessao):
    protocolo = sessao.get("protocolo", "")
    area      = sessao.get("area", "")
    escolha   = mensagem.strip()

    # Limpa sessão — próxima mensagem será novo relato
    sessoes.pop(numero, None)

    if escolha == "1":
        return (
            f"✅ *Caso encaminhado para advogado parceiro.*\n\n"
            f"*Protocolo:* {protocolo}\n"
            f"*Área:* {area}\n\n"
            f"Um advogado receberá seu caso e entrará em contato em breve.\n\n"
            f"Guarde seu protocolo para acompanhamento."
            + DISCLAIMER
        )

    elif escolha == "2":
        return (
            f"✅ *Informações da Defensoria Pública:*\n\n"
            f"{DEFENSORIA_CAMPINAS}\n\n"
            f"*Protocolo do seu caso:* {protocolo}"
            + DISCLAIMER
        )

    elif escolha == "3":
        return (
            f"Tudo bem! Seu caso foi registrado com o protocolo "
            f"*{protocolo}*.\n\n"
            f"Se precisar de ajuda no futuro, é só me enviar uma mensagem."
            + DISCLAIMER
        )

    else:
        # Resposta não reconhecida — mantém estado e pede novamente
        sessoes[numero] = sessao
        return (
            "Não entendi sua resposta. Por favor, escolha:\n\n"
            "1️⃣ Encaminhar para advogado parceiro\n"
            "2️⃣ Informações da Defensoria Pública\n"
            "3️⃣ Não preciso de atendimento agora\n\n"
            "_Responda apenas com o número 1, 2 ou 3._"
        )


# ── Rota de verificação ───────────────────────────────────────────────────────

@app.route("/", methods=['GET'])
def home():
    return "Agente de Triagem Jurídica Online - Sistema Ativo", 200


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)