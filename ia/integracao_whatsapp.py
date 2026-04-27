import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from ia.motor_decisao import MotorDecisao
from banco.banco_dados import salvar_caso

app = Flask(__name__)
motor = MotorDecisao()

@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    # Recebe a mensagem do usuário via Twilio
    mensagem_usuario = request.values.get('Body', '').strip()
    numero_usuario = request.values.get('From', '')

    # Processa a mensagem através do Motor de Decisão Jurídica
    resultado = motor.processar_caso(mensagem_usuario)
    
    # Extrai as informações processadas
    classificacao = resultado['classificacao']
    prioridade = resultado['prioridade']
    acao_sugerida = resultado['acao_sugerida']
    fundamentacao = resultado['fundamentacao']
    protocolo = resultado['protocolo']

    # Salva no banco de dados (SQLite)
    # Nota: No Render, o banco será salvo na pasta definida no seu banco_dados.py
    salvar_caso(
        protocolo=protocolo,
        descricao=mensagem_usuario,
        classificacao=classificacao,
        prioridade=prioridade,
        acao_sugerida=acao_sugerida
    )

    # Prepara a resposta formatada para o WhatsApp
    resposta_texto = (
        f"*Protocolo:* {protocolo}\n\n"
        f"*Triagem:* {classificacao}\n"
        f"*Prioridade:* {prioridade}\n\n"
        f"*Orientação:* {acao_sugerida}\n\n"
        f"*Fundamento Legal:* {fundamentacao}\n\n"
        f"_Este é um serviço de orientação social. Procure sempre um advogado ou a Defensoria Pública._"
    )

    # Cria a resposta no formato TwiML do Twilio
    resp = MessagingResponse()
    resp.message(resposta_texto)

    return str(resp)

@app.route("/", methods=['GET'])
def home():
    return "Agente de Triagem Jurídica Online - Sistema Ativo", 200

if __name__ == "__main__":
    # AJUSTE PARA O RENDER: O servidor define a porta automaticamente
    # Se não houver porta definida (local), usa a 5000
    porta = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' permite que o servidor seja acessado externamente
    app.run(host='0.0.0.0', port=porta)

