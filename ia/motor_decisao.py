class MotorDecisaoJuridica:

    def __init__(self):
        self.regras = {
            "violencia": {
                "palavras": ["agressão", "agressao", "violência", "violencia", "apanhei", "ameaça", "ameaca"],
                "prioridade": 1,
                "acao_sugerida": "Procure imediatamente a Delegacia da Mulher ou a Defensoria Pública.",
                "area": "Direito Penal / Família"
            },
            "trabalhista": {
                "palavras": ["demissão", "demissao", "demitido", "salário", "salario", "rescisão", "rescisao", "empresa", "trabalho", "carteira", "fgts", "assédio", "hora extra"],
                "prioridade": 2,
                "acao_sugerida": "Possível reclamação trabalhista. Procure um advogado ou a Defensoria Pública.",
                "area": "Direito Trabalhista"
            },
            "consumidor": {
                "palavras": ["produto", "defeito", "garantia", "compra", "loja", "entrega", "cobrança", "cobranca", "plano de saúde", "operadora"],
                "prioridade": 3,
                "acao_sugerida": "Possível ação no Juizado Especial Cível (JEC). Procure um advogado.",
                "area": "Direito do Consumidor"
            },
            "bancario": {
                "palavras": ["banco", "cartão", "cartao", "empréstimo", "emprestimo", "financiamento", "juros", "negativação", "negativacao", "serasa", "spc", "fraude"],
                "prioridade": 2,
                "acao_sugerida": "Possível revisão de contrato ou cobrança indevida. Procure um advogado.",
                "area": "Direito Bancário"
            },
            "familia": {
                "palavras": ["divórcio", "divorcio", "separação", "separacao", "guarda", "pensão", "pensao", "alimentos", "filho", "herança", "heranca"],
                "prioridade": 2,
                "acao_sugerida": "Caso de Direito de Família. Procure um advogado ou a Defensoria Pública.",
                "area": "Direito de Família"
            },
            "inss": {
                "palavras": ["inss", "benefício", "beneficio", "aposentadoria", "auxílio", "auxilio", "perícia", "pericia", "bpc", "loas"],
                "prioridade": 2,
                "acao_sugerida": "Possível recurso administrativo ou ação judicial. Procure a Defensoria Pública.",
                "area": "Previdência Social"
            }
        }

    def analisar(self, relato):
        texto = relato.lower()

        resultado = {
            "tipo": "nao_identificado",
            "prioridade": 3,
            "acao_sugerida": "Não foi possível identificar a área jurídica. Procure um advogado ou a Defensoria Pública.",
            "area": "Indefinida"
        }

        for tipo, regra in self.regras.items():
            for palavra in regra["palavras"]:
                if palavra in texto:
                    resultado["tipo"] = tipo
                    resultado["prioridade"] = regra["prioridade"]
                    resultado["acao_sugerida"] = regra["acao_sugerida"]
                    resultado["area"] = regra["area"]
                    return resultado

        # Agora sempre retorna o dicionário, nunca None
        return resultado


agente_decisao = MotorDecisaoJuridica()
