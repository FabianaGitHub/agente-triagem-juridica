class MotorDecisaoJuridica:

    def __init__(self):

        self.regras = {

            "violencia": {
                "palavras": ["agressão", "agressao", "violência", "violencia", "apanhei", "ameaça", "ameaca"],
                "prioridade": 1,
                "acao": "Possível ação de indenização por danos morais",
                "area": "Direito Civil"
            },

            "trabalhista": {
                "palavras": ["demissão", "demissao", "salário", "salario", "empresa", "trabalho", "assédio"],
                "prioridade": 2,
                "acao": "Possível reclamação trabalhista",
                "area": "Direito Trabalhista"
            },

            "consumidor": {
                "palavras": ["produto", "defeito", "garantia", "compra", "loja"],
                "prioridade": 3,
                "acao": "Possível ação no juizado especial cível",
                "area": "Direito do Consumidor"
            },

            "bancario": {
                "palavras": ["banco", "cartão", "cartao", "cobrança", "cobranca", "taxa", "negativação"],
                "prioridade": 2,
                "acao": "Possível revisão de cobrança bancária",
                "area": "Direito Bancário"
            }
        }


    def analisar(self, relato):

        texto = relato.lower()

        resultado = {
            "tipo": "Não identificado",
            "prioridade": 3,
            "acao_sugerida": "Análise manual recomendada",
            "area": "Indefinida"
        }

        for tipo, regra in self.regras.items():

            for palavra in regra["palavras"]:

                if palavra in texto:

                    resultado["tipo"] = tipo
                    resultado["prioridade"] = regra["prioridade"]
                    resultado["acao_sugerida"] = regra["acao"]
                    resultado["area"] = regra["area"]

                    return resultado

        return 
    
    # Adicione esta linha no final do arquivo motor_decisao.py
agente_decisao = MotorDecisaoJuridica()
