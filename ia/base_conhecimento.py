"""
ia/base_conhecimento.py
=======================
Perguntas de triagem e informações de encaminhamento por área jurídica.
"""

# ── Perguntas por (area, sub_area) ────────────────────────────────────────────
# Cada item tem "chave" (salva a resposta), "texto" (mensagem enviada ao usuário)
# e opcionalmente "especial" para tratamento de fluxo condicional.

PERGUNTAS = {
    # ── Direito do Consumidor — cobrança indevida ─────────────────────────────
    ("Direito do Consumidor", "cobranca_indevida"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "tipo_cobranca",
            "texto": (
                "O que foi cobrado indevidamente?\n\n"
                "1️⃣ Produto ou serviço não contratado\n"
                "2️⃣ Valor maior que o combinado\n"
                "3️⃣ Cobrança após cancelamento\n"
                "4️⃣ Cobrança duplicada\n"
                "5️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Produto ou serviço não contratado",
                "2": "Valor maior que o combinado",
                "3": "Cobrança após cancelamento",
                "4": "Cobrança duplicada",
                "5": "Outro"
            }
        },
        {
            "chave": "empresa_contatada",
            "texto": (
                "Você já entrou em contato com a empresa?\n\n"
                "1️⃣ Sim, mas não resolveram\n"
                "2️⃣ Sim, ainda estão analisando\n"
                "3️⃣ Ainda não entrei em contato\n\n"
                "_Responda com 1, 2 ou 3._"
            ),
            "opcoes": {
                "1": "Sim, a empresa não resolveu",
                "2": "Sim, estão analisando",
                "3": "Ainda não"
            }
        },
        {
            "chave": "procon_registrado",
            "texto": (
                "Você já registrou reclamação no Procon ou Consumidor.gov.br?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "comprovante",
            "texto": (
                "Você tem comprovante da cobrança (nota fiscal, extrato, mensagem)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito do Consumidor — produto não entregue ──────────────────────────
    ("Direito do Consumidor", "produto_nao_entregue"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "tipo_compra",
            "texto": (
                "O que foi comprado?\n\n"
                "1️⃣ Produto físico (roupas, eletrônicos, móveis...)\n"
                "2️⃣ Serviço (instalação, reforma, curso...)\n"
                "3️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {"1": "Produto físico", "2": "Serviço", "3": "Outro"}
        },
        {
            "chave": "forma_pagamento",
            "texto": (
                "Qual foi a forma de pagamento?\n\n"
                "1️⃣ PIX à vista\n"
                "2️⃣ Cartão de crédito parcelado\n"
                "3️⃣ Cartão de débito\n"
                "4️⃣ Boleto\n"
                "5️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "PIX à vista",
                "2": "Cartão de crédito parcelado",
                "3": "Cartão de débito",
                "4": "Boleto",
                "5": "Outro"
            }
        },
        {
            "chave": "prazo_estourado",
            "texto": (
                "O prazo de entrega prometido já passou?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não, ainda está no prazo\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim, prazo já passou", "2": "Ainda está no prazo"}
        },
        {
            "chave": "empresa_contatada",
            "texto": (
                "Você já entrou em contato com a empresa sobre a entrega?\n\n"
                "1️⃣ Sim, mas não resolveram\n"
                "2️⃣ Sim, prometeram resolver\n"
                "3️⃣ Ainda não\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, a empresa não resolveu",
                "2": "Sim, prometeram resolver",
                "3": "Ainda não"
            }
        },
        {
            "chave": "comprovante",
            "texto": (
                "Você tem comprovante da compra (nota fiscal, pedido, recibo)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito do Consumidor — plano de saúde ────────────────────────────────
    ("Direito do Consumidor", "plano_saude"): [
        {
            "chave": "o_que_foi_negado",
            "texto": (
                "O que o plano negou?\n\n"
                "1️⃣ Internação ou cirurgia\n"
                "2️⃣ Exame ou diagnóstico\n"
                "3️⃣ Medicamento\n"
                "4️⃣ Consulta com especialista\n"
                "5️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Internação ou cirurgia",
                "2": "Exame ou diagnóstico",
                "3": "Medicamento",
                "4": "Consulta com especialista",
                "5": "Outro"
            }
        },
        {
            "chave": "risco_vida",
            "texto": (
                "A situação envolve urgência médica ou risco de vida?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "especial": "risco_vida",
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "negativa_escrita",
            "texto": (
                "Você tem a negativa por escrito (carta, e-mail, mensagem)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não, foi verbal\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim, tem por escrito", "2": "Não, foi verbal"}
        },
        {
            "chave": "anos_plano",
            "texto": (
                "Há quanto tempo você tem esse plano de saúde?\n\n"
                "1️⃣ Menos de 1 ano\n"
                "2️⃣ Entre 1 e 5 anos\n"
                "3️⃣ Mais de 5 anos\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Menos de 1 ano",
                "2": "Entre 1 e 5 anos",
                "3": "Mais de 5 anos"
            }
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito do Consumidor — geral ─────────────────────────────────────────
    ("Direito do Consumidor", "consumidor_geral"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "tipo_problema",
            "texto": (
                "Qual é o tipo de problema?\n\n"
                "1️⃣ Produto com defeito\n"
                "2️⃣ Serviço mal prestado\n"
                "3️⃣ Propaganda enganosa\n"
                "4️⃣ Dificuldade em cancelar contrato\n"
                "5️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Produto com defeito",
                "2": "Serviço mal prestado",
                "3": "Propaganda enganosa",
                "4": "Dificuldade em cancelar contrato",
                "5": "Outro"
            }
        },
        {
            "chave": "empresa_contatada",
            "texto": (
                "Você já entrou em contato com a empresa?\n\n"
                "1️⃣ Sim, mas não resolveram\n"
                "2️⃣ Sim, estão analisando\n"
                "3️⃣ Ainda não\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, a empresa não resolveu",
                "2": "Sim, estão analisando",
                "3": "Ainda não"
            }
        },
        {
            "chave": "comprovante",
            "texto": (
                "Você tem algum comprovante (nota, contrato, print, recibo)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito Trabalhista ───────────────────────────────────────────────────
    ("Direito Trabalhista", "trabalhista"): [
        {
            "chave": "tipo_problema",
            "texto": (
                "O que aconteceu?\n\n"
                "1️⃣ Fui demitido(a)\n"
                "2️⃣ Salário atrasado ou não pago\n"
                "3️⃣ Horas extras não pagas\n"
                "4️⃣ Acidente de trabalho\n"
                "5️⃣ Assédio ou discriminação\n"
                "6️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Demissão",
                "2": "Salário atrasado ou não pago",
                "3": "Horas extras não pagas",
                "4": "Acidente de trabalho",
                "5": "Assédio ou discriminação",
                "6": "Outro"
            }
        },
        {
            "chave": "carteira_assinada",
            "texto": (
                "Você trabalhava com carteira assinada (CLT)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "ainda_trabalhando",
            "texto": (
                "Você ainda está trabalhando nessa empresa?\n\n"
                "1️⃣ Sim, ainda estou\n"
                "2️⃣ Não, já saí\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim, ainda está trabalhando", "2": "Não, já saiu"}
        },
        {
            "chave": "verbas_rescisoras",
            "texto": (
                "Recebeu as verbas rescisórias (FGTS, aviso prévio, 13º)?\n\n"
                "1️⃣ Sim, recebi tudo\n"
                "2️⃣ Recebi só uma parte\n"
                "3️⃣ Não recebi nada\n"
                "4️⃣ Ainda estou trabalhando lá\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, recebeu tudo",
                "2": "Recebeu parcialmente",
                "3": "Não recebeu nada",
                "4": "Ainda está trabalhando"
            }
        },
        {
            "chave": "ultimo_dia",
            "texto": "Qual foi o último dia de trabalho (ou há quanto tempo trabalha lá)?"
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito de Família — Pensão alimentícia ───────────────────────────────
    ("Direito de Família", "pensao_alimenticia"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "quem_deve",
            "texto": (
                "Quem está sem pagar a pensão?\n\n"
                "1️⃣ O pai da criança\n"
                "2️⃣ A mãe da criança\n"
                "3️⃣ Outro familiar\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "O pai da criança",
                "2": "A mãe da criança",
                "3": "Outro familiar"
            }
        },
        {
            "chave": "acordo_judicial",
            "texto": (
                "Já existe um acordo ou decisão judicial fixando o valor da pensão?\n\n"
                "1️⃣ Sim, tem decisão judicial\n"
                "2️⃣ Sim, tem acordo extrajudicial (em cartório)\n"
                "3️⃣ Não, ainda não foi definido\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, decisão judicial",
                "2": "Sim, acordo em cartório",
                "3": "Não foi definido ainda"
            }
        },
        {
            "chave": "tempo_sem_pagar",
            "texto": (
                "Há quanto tempo está sem receber a pensão?\n\n"
                "1️⃣ Menos de 1 mês\n"
                "2️⃣ Entre 1 e 3 meses\n"
                "3️⃣ Entre 3 e 6 meses\n"
                "4️⃣ Mais de 6 meses\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Menos de 1 mês",
                "2": "Entre 1 e 3 meses",
                "3": "Entre 3 e 6 meses",
                "4": "Mais de 6 meses"
            }
        },
        {
            "chave": "comprovante_falta_pagamento",
            "texto": (
                "Você tem algum comprovante de que não está recebendo "
                "(extratos, mensagens, transferências antigas)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "filhos_menores",
            "texto": (
                "Os filhos que dependem da pensão têm menos de 18 anos?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não, são maiores de 18 (mas ainda dependentes)\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {
                "1": "Sim, menores de 18 anos",
                "2": "Não, maiores de 18 anos"
            }
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito de Família — Divórcio e separação ─────────────────────────────
    ("Direito de Família", "divorcio_separacao"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "tipo_uniao",
            "texto": (
                "Qual é o tipo de relação?\n\n"
                "1️⃣ Casamento registrado em cartório\n"
                "2️⃣ União estável (sem casamento oficial)\n"
                "3️⃣ Não tenho certeza\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Casamento em cartório",
                "2": "União estável",
                "3": "Não tem certeza"
            }
        },
        {
            "chave": "bens_em_comum",
            "texto": (
                "Há bens em comum (casa, carro, conta bancária, empresa)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "filhos_menores",
            "texto": (
                "Há filhos menores de 18 anos?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "acordo_entre_partes",
            "texto": (
                "As duas partes concordam com o divórcio/separação?\n\n"
                "1️⃣ Sim, estamos de acordo\n"
                "2️⃣ Não, há discordância\n"
                "3️⃣ Ainda não conversamos sobre isso\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, consensual",
                "2": "Não, litigioso",
                "3": "Ainda não conversamos"
            }
        },
        {
            "chave": "processo_aberto",
            "texto": (
                "Já existe algum processo judicial em andamento?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito de Família — Guarda de filhos ─────────────────────────────────
    ("Direito de Família", "guarda_filhos"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "situacao_atual",
            "texto": (
                "Qual é a situação agora?\n\n"
                "1️⃣ Quero definir a guarda (ainda não foi definida)\n"
                "2️⃣ Quero mudar a guarda já definida\n"
                "3️⃣ Estão impedindo minhas visitas\n"
                "4️⃣ Quero regularizar as visitas\n"
                "5️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Definir a guarda",
                "2": "Mudar a guarda",
                "3": "Estão impedindo visitas",
                "4": "Regularizar visitas",
                "5": "Outro"
            }
        },
        {
            "chave": "acordo_guarda",
            "texto": (
                "Já existe decisão judicial ou acordo sobre guarda ou visitas?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "idade_crianca",
            "texto": (
                "Qual é a faixa de idade da(s) criança(s) envolvida(s)?\n\n"
                "1️⃣ Até 5 anos\n"
                "2️⃣ Entre 6 e 12 anos\n"
                "3️⃣ Entre 13 e 17 anos\n"
                "4️⃣ 18 anos ou mais\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Até 5 anos",
                "2": "Entre 6 e 12 anos",
                "3": "Entre 13 e 17 anos",
                "4": "18 anos ou mais"
            }
        },
        {
            "chave": "risco_crianca",
            "texto": (
                "A criança corre algum risco de violência ou situação de perigo?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito de Família — Herança e inventário ─────────────────────────────
    ("Direito de Família", "heranca_inventario"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "imovel_envolvido",
            "texto": (
                "Os bens incluem imóvel (casa, terreno ou apartamento)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não, só outros bens\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não, só outros bens"}
        },
        {
            "chave": "inventario_aberto",
            "texto": (
                "Já foi aberto inventário ou processo de partilha?\n\n"
                "1️⃣ Sim, já está em andamento\n"
                "2️⃣ Não foi aberto ainda\n"
                "3️⃣ Não sei informar\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, inventário em andamento",
                "2": "Não foi aberto",
                "3": "Não sabe informar"
            }
        },
        {
            "chave": "herdeiros_concordam",
            "texto": (
                "Os herdeiros estão de acordo sobre a partilha?\n\n"
                "1️⃣ Sim, há acordo\n"
                "2️⃣ Não, há disputa\n"
                "3️⃣ Ainda não conversamos\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, há acordo",
                "2": "Não, há disputa",
                "3": "Ainda não conversaram"
            }
        },
        {
            "chave": "testamento",
            "texto": (
                "A pessoa falecida deixou testamento?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n"
                "3️⃣ Não sei\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {"1": "Sim", "2": "Não", "3": "Não sabe"}
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito de Família — Geral (fallback) ─────────────────────────────────
    ("Direito de Família", "familia"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "tipo_situacao",
            "texto": (
                "Qual é a situação?\n\n"
                "1️⃣ Divórcio ou separação\n"
                "2️⃣ Guarda de filhos\n"
                "3️⃣ Pensão alimentícia\n"
                "4️⃣ Herança ou inventário\n"
                "5️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Divórcio ou separação",
                "2": "Guarda de filhos",
                "3": "Pensão alimentícia",
                "4": "Herança ou inventário",
                "5": "Outro"
            }
        },
        {
            "chave": "filhos_menores",
            "texto": (
                "Há filhos menores de 18 anos envolvidos?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "acordo_existente",
            "texto": (
                "Já existe algum acordo, processo judicial ou decisão sobre isso?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Direito Bancário ──────────────────────────────────────────────────────
    ("Direito Bancário", "bancario"): [
        {
            "chave": "tipo_problema",
            "texto": (
                "O que aconteceu?\n\n"
                "1️⃣ Cobrança indevida ou juros abusivos\n"
                "2️⃣ Nome negativado indevidamente\n"
                "3️⃣ Fraude ou golpe (clonagem, PIX falso)\n"
                "4️⃣ Empréstimo ou desconto não autorizado\n"
                "5️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Cobrança indevida ou juros abusivos",
                "2": "Nome negativado indevidamente",
                "3": "Fraude ou golpe",
                "4": "Empréstimo ou desconto não autorizado",
                "5": "Outro"
            }
        },
        {
            "chave": "banco",
            "texto": "Em qual banco ou instituição financeira ocorreu o problema?"
        },
        {
            "chave": "banco_contatado",
            "texto": (
                "Você já entrou em contato com o banco sobre isso?\n\n"
                "1️⃣ Sim, mas não resolveram\n"
                "2️⃣ Sim, estão analisando\n"
                "3️⃣ Ainda não\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, o banco não resolveu",
                "2": "Sim, estão analisando",
                "3": "Ainda não"
            }
        },
        {
            "chave": "boletim_ocorrencia",
            "texto": (
                "Você registrou boletim de ocorrência (para casos de fraude ou golpe)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n"
                "3️⃣ Não se aplica ao meu caso\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, B.O. registrado",
                "2": "Não registrou",
                "3": "Não se aplica"
            }
        },
        {
            "chave": "comprovante",
            "texto": (
                "Você tem comprovante do problema (extrato, print, notificação)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "opcoes": {"1": "Sim", "2": "Não"}
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],

    # ── Previdência Social ────────────────────────────────────────────────────
    ("Previdência Social", "inss"): [
        {
            "chave": "tipo_beneficio",
            "texto": (
                "Qual benefício está envolvido?\n\n"
                "1️⃣ Aposentadoria por tempo ou idade\n"
                "2️⃣ Auxílio-doença ou afastamento\n"
                "3️⃣ BPC/LOAS (benefício assistencial)\n"
                "4️⃣ Pensão por morte\n"
                "5️⃣ Outro\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Aposentadoria",
                "2": "Auxílio-doença ou afastamento",
                "3": "BPC/LOAS",
                "4": "Pensão por morte",
                "5": "Outro"
            }
        },
        {
            "chave": "foi_ao_inss",
            "texto": (
                "Você já compareceu ao INSS pessoalmente ou ligou para o 135?\n\n"
                "1️⃣ Sim, já fui / já liguei\n"
                "2️⃣ Ainda não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "especial": "foi_inss",
            "opcoes": {"1": "Sim, já foi / já ligou", "2": "Ainda não"}
        },
        {
            "chave": "beneficio_negado",
            "texto": (
                "O benefício foi negado ou cancelado?\n\n"
                "1️⃣ Sim, foi negado\n"
                "2️⃣ Sim, foi cancelado\n"
                "3️⃣ Ainda não recebi resposta\n"
                "4️⃣ Outro problema\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Benefício negado",
                "2": "Benefício cancelado",
                "3": "Sem resposta ainda",
                "4": "Outro"
            }
        },
        {
            "chave": "tempo_contribuicao",
            "texto": (
                "Você tem ou teve carteira assinada (contribuiu para o INSS)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não, trabalho(ei) por conta própria\n"
                "3️⃣ Nunca contribuí\n\n"
                "_Responda com o número._"
            ),
            "opcoes": {
                "1": "Sim, com carteira assinada",
                "2": "Trabalhou por conta própria",
                "3": "Nunca contribuiu"
            }
        },
        {
            "chave": "info_adicional",
            "texto": (
                "Tem mais alguma informação importante que ainda não disse?\n\n"
                "_Se sim, descreva. Se não, responda \"Não\"._"
            )
        },
    ],
}


def obter_perguntas(area, sub_area):
    return PERGUNTAS.get((area, sub_area), [])


# ── Informações de encaminhamento ─────────────────────────────────────────────

CEJUSC_INFO = (
    "⚖️ *CEJUSC — Centro Judiciário de Solução de Conflitos*\n"
    "Oferece mediação e conciliação de forma gratuita.\n"
    "Procure o CEJUSC no fórum da sua cidade.\n"
    "Mais informações: www.tjsp.jus.br/CEJUSC"
)

PROCON_INFO = (
    "📣 *Procon*\n"
    "Ligue *151* (gratuito, segunda a sexta)\n"
    "Registre online: www.consumidor.gov.br\n"
    "Ou procure o Procon da sua cidade para atendimento presencial."
)

JEC_INFO = (
    "🏛️ *Juizado Especial Cível (JEC)*\n"
    "Atende causas de até 40 salários mínimos, sem necessidade de advogado.\n"
    "Procure o Juizado Especial no fórum da sua cidade."
)

ANS_INFO = (
    "📋 *ANS — Agência Nacional de Saúde Suplementar*\n"
    "Registre sua reclamação:\n"
    "📞 0800 701 9656 (gratuito)\n"
    "🌐 www.ans.gov.br/consumidor"
)

MEU_INSS_INFO = (
    "📱 *Meu INSS*\n"
    "Acesse pelo app *Meu INSS* ou pelo site *meu.inss.gov.br*\n"
    "Lá você pode solicitar benefícios, verificar extratos e agendar perícias.\n"
    "Central de atendimento: *135* (gratuito)"
)


# Mantido para compatibilidade com a interface desktop
def obter_orientacao_legal(area):
    return {"fundamento": "", "explicacao": ""}
