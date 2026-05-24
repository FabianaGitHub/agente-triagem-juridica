"""
ia/classificador_casos.py
=========================
Módulo de Classificação Jurídica com Machine Learning (scikit-learn)
"""

import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATASET_PATH, CATEGORIAS_JURIDICAS
from ia.analisador_texto import processar_texto

try:
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    _SKLEARN_DISPONIVEL = True
except ImportError:
    _SKLEARN_DISPONIVEL = False

_modelo_treinado = None


def _carregar_dataset() -> tuple:
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset não encontrado em: {DATASET_PATH}\n"
            "Verifique se o arquivo 'dados/treinamento_casos.csv' existe."
        )

    textos = []
    rotulos = []

    with open(DATASET_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            relato = linha.get("relato", "").strip()
            tipo = linha.get("tipo_caso", "").strip()
            if relato and tipo:
                textos.append(processar_texto(relato))
                rotulos.append(tipo)

    return textos, rotulos


def treinar_modelo():
    global _modelo_treinado

    if not _SKLEARN_DISPONIVEL:
        raise ImportError(
            "scikit-learn não está instalado. "
            "Execute: pip install scikit-learn"
        )

    textos, rotulos = _carregar_dataset()

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_features=5000,
            sublinear_tf=True,
        )),
        ("classificador", MultinomialNB(alpha=0.5)),
    ])

    pipeline.fit(textos, rotulos)
    _modelo_treinado = pipeline
    print(f"[Classificador] Modelo treinado com {len(textos)} exemplos.")
    return pipeline


def classificar_caso(relato: str) -> str:
    global _modelo_treinado
    try:
        # Import corrigido — sem 'projeto_juridico.'
        from ia.motor_decisao import agente_decisao
        decisao = agente_decisao.analisar(relato)
        if decisao["area"] != "Indefinida":
            return decisao["area"]

        if _modelo_treinado is None:
            treinar_modelo()

        texto_processado = processar_texto(relato)
        predicao = _modelo_treinado.predict([texto_processado])
        return predicao[0]
    except Exception as e:
        print(f"[Classificador] Erro: {e}")
        return _classificar_por_palavras_chave(relato)


def _classificar_por_palavras_chave(relato: str) -> str:
    relato_lower = relato.lower()

    palavras_consumidor = [
        "produto", "defeito", "troca", "devolução", "loja", "compra",
        "entrega", "fornecedor", "consumidor", "serviço", "cobrança indevida",
        "plano de saúde", "operadora", "companhia aérea", "construtora",
    ]
    palavras_trabalhista = [
        "demissão", "demitido", "trabalho", "emprego", "salário", "carteira",
        "rescisão", "fgts", "horas extras", "insalubridade", "assédio",
        "empresa", "empregador", "contrato trabalho", "justa causa",
    ]
    palavras_familia = [
        "divórcio", "separação", "guarda", "filhos", "pensão", "alimentos",
        "herança", "inventário", "adoção", "paternidade", "cônjuge",
        "casamento", "violência doméstica", "medida protetiva",
    ]
    palavras_bancario = [
        "banco", "empréstimo", "financiamento", "juros", "negativação",
        "spc", "serasa", "cartão", "conta", "fraude bancária", "débito",
        "crédito", "boleto", "tarifas", "seguro prestamista",
    ]

    pontos = {
        "Direito do Consumidor": sum(1 for p in palavras_consumidor if p in relato_lower),
        "Direito Trabalhista":   sum(1 for p in palavras_trabalhista if p in relato_lower),
        "Direito de Família":    sum(1 for p in palavras_familia if p in relato_lower),
        "Direito Bancário":      sum(1 for p in palavras_bancario if p in relato_lower),
    }

    melhor = max(pontos, key=pontos.get)
    if pontos[melhor] > 0:
        return melhor
    return "Não classificado"


def obter_probabilidades(relato: str) -> dict:
    global _modelo_treinado

    try:
        if _modelo_treinado is None:
            treinar_modelo()

        texto_processado = processar_texto(relato)
        probabilidades = _modelo_treinado.predict_proba([texto_processado])[0]
        classes = _modelo_treinado.classes_

        resultado = {
            classe: round(float(prob) * 100, 1)
            for classe, prob in zip(classes, probabilidades)
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    except Exception:
        return {}
