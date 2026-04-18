"""
ia/classificador_casos.py
=========================
Módulo de Classificação Jurídica com Machine Learning (scikit-learn)

Este módulo implementa um classificador de texto utilizando a abordagem
TF-IDF + Naive Bayes, amplamente utilizada em tarefas de classificação
de documentos textuais.

Conceitos utilizados:
    - TF-IDF (Term Frequency–Inverse Document Frequency): técnica de
      vetorização que transforma texto em números, dando mais peso às
      palavras que são frequentes em um documento mas raras no corpus.
    - Naive Bayes Multinomial: algoritmo probabilístico baseado no Teorema
      de Bayes, muito eficiente para classificação de textos curtos.

O modelo é treinado com o dataset localizado em dados/treinamento_casos.csv
e classifica os relatos em quatro categorias jurídicas:
    - Direito do Consumidor
    - Direito Trabalhista
    - Direito de Família
    - Direito Bancário

Funções disponíveis:
    - treinar_modelo(): treina e retorna o pipeline de classificação.
    - classificar_caso(relato): classifica um relato e retorna a categoria.
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
    from sklearn.preprocessing import LabelEncoder
    _SKLEARN_DISPONIVEL = True
except ImportError:
    _SKLEARN_DISPONIVEL = False

# Variável global que armazena o modelo treinado (cache em memória)
_modelo_treinado = None


def _carregar_dataset() -> tuple:
    """
    Carrega o dataset de treinamento do arquivo CSV.

    Retorna:
        tuple: (textos, rotulos) — listas com os relatos e suas categorias.

    Lança:
        FileNotFoundError: se o arquivo CSV não for encontrado.
    """
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
                # Aplica pré-processamento NLP antes do treinamento
                textos.append(processar_texto(relato))
                rotulos.append(tipo)

    return textos, rotulos


def treinar_modelo():
    """
    Treina o pipeline de classificação TF-IDF + Naive Bayes.

    O pipeline encadeia automaticamente:
    1. TfidfVectorizer: converte texto processado em vetor numérico TF-IDF.
    2. MultinomialNB: classifica o vetor na categoria jurídica correta.

    O modelo treinado é armazenado em cache na variável global
    _modelo_treinado para evitar retreinamento a cada classificação.

    Retorna:
        Pipeline: modelo treinado pronto para uso.
    """
    global _modelo_treinado

    if not _SKLEARN_DISPONIVEL:
        raise ImportError(
            "scikit-learn não está instalado. "
            "Execute: pip install scikit-learn"
        )

    textos, rotulos = _carregar_dataset()

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),   # Usa unigramas e bigramas
            min_df=1,             # Mínimo de documentos para incluir um termo
            max_features=5000,    # Limita o vocabulário a 5000 termos
            sublinear_tf=True,    # Aplica escala logarítmica ao TF
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
        # 1. Consulta o Agente (Motor de Decisão) - Prioridade Máxima
        from projeto_juridico.ia.motor_decisao import agente_decisao
        decisao = agente_decisao.analisar(relato)
        if decisao["area"] != "Indefinida":
            return decisao["area"]

        # 2. Fallback para Machine Learning
        if _modelo_treinado is None:
            treinar_modelo()

        texto_processado = processar_texto(relato)
        predicao = _modelo_treinado.predict([texto_processado])
        return predicao[0]
    except Exception as e:
        print(f"[Classificador] Erro: {e}")
        return _classificar_por_palavras_chave(relato)

def _classificar_por_palavras_chave(relato: str) -> str:
    """
    Classificação de fallback baseada em palavras-chave.

    Utilizada quando o modelo de ML não está disponível ou falha.
    Analisa a presença de termos jurídicos específicos no relato.

    Parâmetros:
        relato (str): Texto do relato jurídico.

    Retorna:
        str: Categoria jurídica identificada ou "Não classificado".
    """
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
        "Direito Trabalhista": sum(1 for p in palavras_trabalhista if p in relato_lower),
        "Direito de Família": sum(1 for p in palavras_familia if p in relato_lower),
        "Direito Bancário": sum(1 for p in palavras_bancario if p in relato_lower),
    }

    melhor = max(pontos, key=pontos.get)
    if pontos[melhor] > 0:
        return melhor
    return "Não classificado"


def obter_probabilidades(relato: str) -> dict:
    """
    Retorna as probabilidades de cada categoria para um dado relato.

    Útil para exibir o nível de confiança da classificação na interface.

    Parâmetros:
        relato (str): Texto bruto do relato jurídico.

    Retorna:
        dict: Dicionário {categoria: probabilidade} ordenado por confiança.
    """
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
