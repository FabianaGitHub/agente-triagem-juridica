"""
ia/base_conhecimento.py
=======================
Base de Conhecimento Jurídico para o Chatbot.
"""

BASE_LEGAL = {
    "Direito do Consumidor": {
        "fundamento": "Art. 14 e 18 do Código de Defesa do Consumidor (CDC).",
        "explicacao": "O fornecedor responde pela reparação dos danos causados aos consumidores por defeitos relativos à prestação dos serviços ou vícios do produto.",
    },
    "Direito Trabalhista": {
        "fundamento": "Art. 477 e 487 da Consolidação das Leis do Trabalho (CLT).",
        "explicacao": "Estabelece prazos para pagamento de verbas rescisórias e regras sobre aviso prévio em caso de demissão sem justa causa.",
    },
    "Direito de Família": {
        "fundamento": "Art. 1.571 e 1.694 do Código Civil Brasileiro.",
        "explicacao": "Trata da dissolução da sociedade conjugal e do direito a alimentos (pensão) com base no binômio necessidade-possibilidade.",
    },
    "Direito Bancário": {
        "fundamento": "Súmula 297 do STJ e Art. 52 do CDC.",
        "explicacao": "O Código de Defesa do Consumidor é aplicável às instituições financeiras, limitando juros abusivos e taxas não contratadas.",
    },
    "Direito Penal / Família": {
        "fundamento": "Lei 11.340/2006 (Lei Maria da Penha).",
        "explicacao": "Cria mecanismos para coibir a violência doméstica e familiar contra a mulher, prevendo medidas protetivas de urgência.",
    }
}

def obter_orientacao_legal(area):
    return BASE_LEGAL.get(area, {
        "fundamento": "Legislação Civil Geral.",
        "explicacao": "O caso requer análise detalhada do Código Civil e normas específicas."
    })
