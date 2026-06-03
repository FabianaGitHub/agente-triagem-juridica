class MotorDecisaoJuridica:

    def __init__(self):
        # Sub-áreas específicas de Consumidor vêm antes do genérico
        self.regras = {
            "plano_saude": {
                "palavras": ["plano de saúde", "plano de saude", "operadora", "convênio médico",
                             "convenio medico", "plano negou", "negou procedimento",
                             "negou internação", "negou internacao"],
                "prioridade": 2,
                "area": "Direito do Consumidor",
                "sub_area": "plano_saude",
                "acao_sugerida": "Verifique os direitos previstos no contrato e na ANS."
            },
            "cobranca_indevida": {
                "palavras": ["cobrança indevida", "cobranca indevida", "cobrado indevidamente",
                             "valor não contratado", "valor nao contratado", "taxa indevida",
                             "desconto indevido", "cobrado a mais"],
                "prioridade": 3,
                "area": "Direito do Consumidor",
                "sub_area": "cobranca_indevida",
                "acao_sugerida": "Possível ação no Procon ou Juizado Especial Cível."
            },
            "produto_nao_entregue": {
                "palavras": ["não entregou", "nao entregou", "produto não chegou",
                             "produto nao chegou", "serviço não prestado", "servico nao prestado",
                             "não cumpriu prazo", "nao cumpriu prazo"],
                "prioridade": 3,
                "area": "Direito do Consumidor",
                "sub_area": "produto_nao_entregue",
                "acao_sugerida": "Possível ação no Procon ou Juizado Especial Cível."
            },
            "consumidor": {
                "palavras": ["produto", "defeito", "garantia", "compra", "loja", "entrega",
                             "cobrança", "cobranca", "fornecedor", "nota fiscal", "troca"],
                "prioridade": 3,
                "area": "Direito do Consumidor",
                "sub_area": "consumidor_geral",
                "acao_sugerida": "Possível ação no Juizado Especial Cível (JEC)."
            },
            "trabalhista": {
                "palavras": ["demissão", "demissao", "demitido", "salário", "salario",
                             "rescisão", "rescisao", "carteira assinada", "fgts", "assédio",
                             "hora extra", "aviso prévio", "aviso previo", "trabalhista"],
                "prioridade": 2,
                "area": "Direito Trabalhista",
                "sub_area": "trabalhista",
                "acao_sugerida": "Possível reclamação trabalhista. Procure um advogado."
            },
            "bancario": {
                "palavras": ["banco", "cartão", "cartao", "empréstimo", "emprestimo",
                             "financiamento", "juros", "negativação", "negativacao",
                             "serasa", "spc", "fraude bancária", "fraude bancaria"],
                "prioridade": 2,
                "area": "Direito Bancário",
                "sub_area": "bancario",
                "acao_sugerida": "Possível revisão de contrato ou cobrança indevida."
            },
            "familia": {
                "palavras": ["divórcio", "divorcio", "separação", "separacao", "guarda",
                             "pensão alimentícia", "pensao alimenticia", "alimentos",
                             "herança", "heranca", "inventário", "inventario"],
                "prioridade": 2,
                "area": "Direito de Família",
                "sub_area": "familia",
                "acao_sugerida": "Procure um advogado ou a Defensoria Pública."
            },
            "inss": {
                "palavras": ["inss", "benefício", "beneficio", "aposentadoria",
                             "auxílio doença", "auxilio doenca", "perícia", "pericia",
                             "bpc", "loas", "previdência social", "previdencia social"],
                "prioridade": 2,
                "area": "Previdência Social",
                "sub_area": "inss",
                "acao_sugerida": "Verifique no Meu INSS ou procure um advogado."
            }
        }

    def analisar(self, relato):
        texto = relato.lower()

        resultado = {
            "tipo": "nao_identificado",
            "prioridade": 3,
            "area": "Indefinida",
            "sub_area": "indefinida",
            "acao_sugerida": "Não foi possível identificar a área jurídica."
        }

        for tipo, regra in self.regras.items():
            for palavra in regra["palavras"]:
                if palavra in texto:
                    resultado["tipo"]          = tipo
                    resultado["prioridade"]    = regra["prioridade"]
                    resultado["area"]          = regra["area"]
                    resultado["sub_area"]      = regra["sub_area"]
                    resultado["acao_sugerida"] = regra["acao_sugerida"]
                    return resultado

        return resultado


agente_decisao = MotorDecisaoJuridica()
