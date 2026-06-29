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
                             "herança", "heranca", "inventário", "inventario",
                             "falecido", "falecida", "faleceu", "espólio", "espolio",
                             "avô", "avó", "avo", "ava", "pai faleceu", "mãe faleceu",
                             "imóvel", "imovel", "terreno", "escritura", "partilha",
                             "sucessão", "sucessao", "testamento", "viúvo", "viuvo",
                             "viúva", "viuva", "cônjuge", "conjuge"],
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

        melhor_tipo   = None
        melhor_regra  = None
        melhor_contagem = 0

        for tipo, regra in self.regras.items():
            contagem = sum(1 for p in regra["palavras"] if p in texto)
            if contagem > melhor_contagem:
                melhor_contagem = contagem
                melhor_tipo     = tipo
                melhor_regra    = regra

        if melhor_regra:
            return {
                "tipo":          melhor_tipo,
                "prioridade":    melhor_regra["prioridade"],
                "area":          melhor_regra["area"],
                "sub_area":      melhor_regra["sub_area"],
                "acao_sugerida": melhor_regra["acao_sugerida"]
            }

        return {
            "tipo":          "nao_identificado",
            "prioridade":    3,
            "area":          "Indefinida",
            "sub_area":      "indefinida",
            "acao_sugerida": "Não foi possível identificar a área jurídica."
        }


agente_decisao = MotorDecisaoJuridica()
