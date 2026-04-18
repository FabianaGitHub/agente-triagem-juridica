from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
from datetime import datetime

# Importações do seu projeto
from ia.motor_decisao import agente_decisao
from ia.base_conhecimento import obter_orientacao_legal
from banco.banco_dados import gerar_id_sequencial, inserir_caso

app = Flask(__name__)

# Dicionário temporário para controlar o estado da conversa de cada número de WhatsApp
# Em um sistema real, isso seria salvo no banco de dados
estados_conversa = {}

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    """Função principal que recebe e responde as mensagens do WhatsApp."""
    numero_whatsapp = request.form.get('From')
    mensagem_usuario = request.form.get('Body', '').strip()
    
    # Inicializa o estado se for um novo número
    if numero_whatsapp not in estados_conversa:
        estados_conversa[numero_whatsapp] = {"etapa": "INICIO", "nome": "", "relato": ""}

    estado = estados_conversa[numero_whatsapp]
    response = MessagingResponse()
    msg = response.message()

    # --- FLUXO DE CONVERSA ÉTICO ---
    
    if estado["etapa"] == "INICIO":
        texto_boas_vindas = (
            "⚖️ *Assistente Virtual - Projeto ACESSUS*\n\n"
            "Olá! Sou um assistente de triagem automatizado. Meu objetivo é organizar seu relato para que nossos advogados parceiros possam te ajudar.\n\n"
            "⚠️ *AVISO IMPORTANTE:* Este sistema realiza apenas uma triagem inicial. Não fornecemos consultoria jurídica definitiva. Todo caso será revisado por um advogado inscrito na OAB.\n\n"
            "Para começarmos, como posso te chamar?"
        )
        msg.body(texto_boas_vindas)
        estado["etapa"] = "NOME"

    elif estado["etapa"] == "NOME":
        estado["nome"] = mensagem_usuario
        texto_relato = (
            f"Prazer em te conhecer, {estado['nome']}!\n\n"
            "Agora, por favor, descreva o seu problema jurídico com o máximo de detalhes (ex: o que aconteceu, datas, valores envolvidos)."
        )
        msg.body(texto_relato)
        estado["etapa"] = "RELATO"

    elif estado["etapa"] == "RELATO":
        estado["relato"] = mensagem_usuario
        
        # 1. O Agente analisa o relato
        decisao = agente_decisao.analisar(estado["relato"])
        area = decisao["area"]
        acao = decisao["acao_sugerida"]
        
        # 2. Busca fundamento legal na Base de Conhecimento
        orientacao = obter_orientacao_legal(area)
        
        # 3. Gera o Protocolo Sincronizado (ex: 001_2026)
        id_protocolo = gerar_id_sequencial()
        
        # 4. Salva no Banco de Dados automaticamente
        inserir_caso(
            id_protocolo, 
            estado["nome"], 
            "WhatsApp", # Email
            numero_whatsapp, # WhatsApp
            estado["relato"], 
            area, 
            f"Prioridade {decisao['prioridade']}", 
            "" # Sem anexos via WhatsApp por enquanto
        )

        # 5. Resposta Final Fundamentada
        texto_final = (
            f"✅ *Triagem Concluída com Sucesso!*\n\n"
            f"🆔 *Protocolo:* {id_protocolo}\n"
            f"📂 *Área Identificada:* {area}\n\n"
            f"⚖️ *Fundamento Legal:* {orientacao['fundamento']}\n"
            f"📖 *O que a lei diz:* {orientacao['explicacao']}\n\n"
            f"💡 *Próximo Passo:* {acao}\n\n"
            "Seu relato já foi enviado para nossos advogados parceiros. Eles entrarão em contato em breve. Deseja algo mais?"
        )
        msg.body(texto_final)
        # Reinicia o estado para um novo atendimento futuro
        estados_conversa[numero_whatsapp] = {"etapa": "INICIO", "nome": "", "relato": ""}

    return str(response)

if __name__ == "__main__":
    # O Flask rodará na porta 5000 do seu computador
    app.run(port=5000, debug=True)
