"""
ia/base_conhecimento.py
=======================
Perguntas de triagem e informações de encaminhamento por área jurídica.
"""

# ── Perguntas por (area, sub_area) ────────────────────────────────────────────
# Cada item tem "chave" (salva a resposta), "texto" (mensagem enviada ao usuário)
# e opcionalmente "especial" para tratamento de fluxo condicional.

PERGUNTAS = {
    ("Direito do Consumidor", "cobranca_indevida"): [
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
        {
            "chave": "descricao_cobranca",
            "texto": "O que foi cobrado indevidamente? Descreva brevemente."
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
                "_Responda com o número ou descreva._"
            )
        },
        {
            "chave": "data",
            "texto": "Qual foi a data aproximada da cobrança?"
        },
        {
            "chave": "retorno_empresa",
            "texto": "Você já entrou em contato com a empresa? Se sim, qual foi a resposta?"
        },
    ],
    ("Direito do Consumidor", "produto_nao_entregue"): [
        {
            "chave": "item_comprado",
            "texto": "O que foi comprado (produto ou serviço)?"
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
                "_Responda com o número ou descreva._"
            )
        },
        {
            "chave": "datas",
            "texto": "Qual foi a data da compra e o prazo prometido para entrega?"
        },
        {
            "chave": "retorno_empresa",
            "texto": "Você já entrou em contato com a empresa? Se sim, qual foi a resposta?"
        },
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
    ],
    ("Direito do Consumidor", "plano_saude"): [
        {
            "chave": "o_que_foi_negado",
            "texto": "O que foi negado pelo plano? (procedimento, internação, medicamento, exame...)"
        },
        {
            "chave": "risco_vida",
            "texto": (
                "A situação envolve urgência médica ou risco de vida?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "especial": "risco_vida"
        },
        {
            "chave": "negativa_escrita",
            "texto": "Você tem a negativa por escrito (carta, e-mail, mensagem)?"
        },
    ],
    ("Direito do Consumidor", "consumidor_geral"): [
        {
            "chave": "descricao",
            "texto": "Pode me contar mais detalhes sobre o que aconteceu?"
        },
        {
            "chave": "data",
            "texto": "Qual foi a data aproximada?"
        },
        {
            "chave": "retorno_empresa",
            "texto": "Você já entrou em contato com a empresa? Se sim, qual foi a resposta?"
        },
        {
            "chave": "cidade",
            "texto": "Em qual cidade você está?"
        },
    ],
    ("Direito Trabalhista", "trabalhista"): [
        {
            "chave": "descricao",
            "texto": "O que aconteceu? (demissão, salário atrasado, horas extras não pagas, outro)"
        },
        {
            "chave": "carteira_assinada",
            "texto": (
                "Você trabalhava com carteira assinada (CLT)?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            )
        },
        {
            "chave": "ultimo_dia",
            "texto": "Qual foi o último dia de trabalho (ou ainda está trabalhando)?"
        },
        {
            "chave": "situacao_rescisao",
            "texto": "Você recebeu algum valor na rescisão ou ainda está aguardando?"
        },
    ],
    ("Direito de Família", "familia"): [
        {
            "chave": "tipo_situacao",
            "texto": "Qual é a situação? (divórcio, guarda de filhos, pensão alimentícia, herança, outro)"
        },
        {
            "chave": "filhos_menores",
            "texto": (
                "Há filhos menores envolvidos?\n\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "_Responda com 1 ou 2._"
            )
        },
        {
            "chave": "acordo_existente",
            "texto": "Já existe algum acordo ou processo judicial em andamento?"
        },
    ],
    ("Direito Bancário", "bancario"): [
        {
            "chave": "descricao",
            "texto": "O que aconteceu? (cobrança indevida, juros abusivos, negativação indevida, fraude, outro)"
        },
        {
            "chave": "banco",
            "texto": "Em qual banco ou instituição financeira?"
        },
        {
            "chave": "data",
            "texto": "Qual foi a data aproximada do ocorrido?"
        },
        {
            "chave": "retorno_banco",
            "texto": "Você já entrou em contato com o banco? Se sim, qual foi a resposta?"
        },
    ],
    ("Previdência Social", "inss"): [
        {
            "chave": "beneficio",
            "texto": "Qual benefício está envolvido? (aposentadoria, auxílio-doença, BPC/LOAS, outro)"
        },
        {
            "chave": "foi_ao_inss",
            "texto": (
                "Você já compareceu ao INSS pessoalmente ou ligou para o 135?\n\n"
                "1️⃣ Sim, já fui / já liguei\n"
                "2️⃣ Ainda não\n\n"
                "_Responda com 1 ou 2._"
            ),
            "especial": "foi_inss"
        },
        {
            "chave": "situacao_inss",
            "texto": "Qual foi a resposta ou situação atual no INSS?"
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
