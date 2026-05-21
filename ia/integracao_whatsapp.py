import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from ia.motor_decisao import MotorDecisaoJuridica as MotorDecisao
from ia.base_conhecimento import obter_orientacao_legal
from banco.banco_dados import salvar_caso, criar_banco

app = Flask(__name__)
motor = MotorDecisao()

# Garante que o banco existe ao iniciar
criar_banco()

@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    mensagem_usuario = request.values.get('Body', '').strip()
    numero_usuario = request.values.get('From', '')

    # Usa o método correto — analisar()
    resultado = motor.analisar(mensagem_usuario)

    area = resultado.get('area', 'Indefinida')
    prioridade = resultado.get('prioridade', 3)
    acao_sugerida = resultado.get('acao_sugerida', 'Procure um advogado ou a Defensoria Pública.')

    # Busca orientação legal da base de conhecimento
    orientacao = obter_orientacao_legal(area)
    fundamento = orientacao.get('fundamento', '')
    explicacao = orientacao.get('explicacao', '')

    # Gera protocolo e salva no banco
    from banco.banco_dados import gerar_id_sequencial
    protocolo = gerar_id_sequencial()

    salvar_caso(
        protocolo=protocolo,
        descricao=mensagem_usuario,
        classificacao=area,
        prioridade=f"Prioridade {prioridade}",
        acao_sugerida=acao_sugerida
    )

    # Monta resposta para o WhatsApp
    resposta_texto = (
        f"*Protocolo:* {protocolo}\n\n"
        f"*Área identificada:* {area}\n\n"
        f"⚖️ *Fundamento legal:* {fundamento}\n"
        f"📖 *O que a lei diz:* {explicacao}\n\n"
        f"💡 *Orientação:* {acao_sugerida}\n\n"
        f"Deseja encaminhar seu caso?\n"
        f"1️⃣ Advogado parceiro\n"
        f"2️⃣ Defensoria Pública\n"
        f"3️⃣ Não preciso agora\n\n"
        f"_Este serviço presta orientação informativa. Para assessoria jurídica, procure sempre um advogado._"
    )

    resp = MessagingResponse()
    resp.message(resposta_texto)
    return str(resp)

@app.route("/", methods=['GET'])
def home():
    return "Agente de Triagem Jurídica Online - Sistema Ativo", 200

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
