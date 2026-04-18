"""
ia/analisador_texto.py
======================
Módulo de Análise de Texto com NLP (spaCy)

Este módulo implementa o pré-processamento de linguagem natural utilizando a
biblioteca spaCy com o modelo de português. O processamento de linguagem natural
(NLP — Natural Language Processing) é uma subárea da Inteligência Artificial que
lida com a interação entre computadores e a linguagem humana.

As etapas realizadas neste módulo são:
    1. Limpeza do texto (remoção de caracteres especiais e normalização)
    2. Tokenização (divisão do texto em unidades menores — tokens)
    3. Remoção de stopwords (palavras sem valor semântico como "de", "a", "o")
    4. Lematização (redução das palavras à sua forma base/raiz)

Função principal:
    - processar_texto(relato): recebe um relato em texto e retorna o texto
      processado, pronto para ser utilizado pelo classificador.
"""

import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SPACY_MODEL

# Carregamento do modelo spaCy — feito uma única vez ao importar o módulo
try:
    import spacy
    _nlp = spacy.load(SPACY_MODEL)
    _SPACY_DISPONIVEL = True
except Exception:
    _SPACY_DISPONIVEL = False
    _nlp = None


def _limpar_texto(texto: str) -> str:
    """
    Realiza a limpeza básica do texto:
    - Converte para letras minúsculas
    - Remove caracteres especiais, pontuação e números
    - Remove espaços extras

    Parâmetros:
        texto (str): Texto bruto de entrada.

    Retorna:
        str: Texto limpo e normalizado.
    """
    texto = texto.lower()
    # Remove caracteres que não sejam letras ou espaços
    texto = re.sub(r"[^a-záàâãéêíóôõúüçñ\s]", " ", texto)
    # Remove espaços múltiplos
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def processar_texto(relato: str) -> str:
    """
    Processa um relato jurídico aplicando técnicas de NLP.

    O processamento inclui:
    1. Limpeza e normalização do texto.
    2. Tokenização via spaCy (se disponível) ou por espaços.
    3. Remoção de stopwords (palavras sem valor semântico).
    4. Lematização (redução à forma base da palavra).

    Parâmetros:
        relato (str): Texto bruto do relato jurídico.

    Retorna:
        str: Texto processado, com tokens significativos separados por espaço.
             Este texto é usado como entrada para o classificador de casos.

    Exemplo:
        >>> processar_texto("Fui demitido sem justa causa pela empresa")
        'demitido justa causa empresa'
    """
    texto_limpo = _limpar_texto(relato)

    if _SPACY_DISPONIVEL and _nlp is not None:
        doc = _nlp(texto_limpo)
        tokens = [
            token.lemma_
            for token in doc
            if not token.is_stop          # Remove stopwords
            and not token.is_punct        # Remove pontuação
            and not token.is_space        # Remove espaços
            and len(token.lemma_) > 2     # Remove tokens muito curtos
        ]
    else:
        # Fallback: tokenização simples por espaços sem spaCy
        stopwords_pt = {
            "de", "a", "o", "que", "e", "do", "da", "em", "um", "para",
            "com", "uma", "os", "no", "se", "na", "por", "mais", "as",
            "dos", "como", "mas", "ao", "ele", "das", "seu", "sua", "ou",
            "quando", "muito", "nos", "já", "eu", "também", "só", "pelo",
            "pela", "até", "isso", "ela", "entre", "depois", "sem", "mesmo",
            "aos", "seus", "quem", "nas", "me", "esse", "eles", "você",
            "essa", "num", "nem", "suas", "meu", "às", "minha", "têm",
            "numa", "pelos", "elas", "havia", "seja", "qual", "será",
            "nós", "tenho", "lhe", "deles", "essas", "esses", "pelas",
            "este", "dele", "tu", "te", "vocês", "vos", "lhes", "meus",
            "minhas", "teu", "tua", "teus", "tuas", "nosso", "nossa",
            "nossos", "nossas", "dela", "delas", "esta", "estes", "estas",
            "aquele", "aquela", "aqueles", "aquelas", "isto", "aquilo",
            "estou", "está", "estamos", "estão", "estive", "esteve",
            "foi", "foram", "ser", "ter", "haver", "estar", "sendo",
        }
        tokens = [
            palavra
            for palavra in texto_limpo.split()
            if palavra not in stopwords_pt and len(palavra) > 2
        ]

    return " ".join(tokens)


def extrair_palavras_chave(relato: str, top_n: int = 5) -> list:
    """
    Extrai as palavras-chave mais relevantes de um relato.

    Utiliza a lematização e filtragem de stopwords para identificar
    os termos com maior valor semântico no texto.

    Parâmetros:
        relato (str): Texto bruto do relato jurídico.
        top_n  (int): Número máximo de palavras-chave a retornar.

    Retorna:
        list[str]: Lista com as principais palavras-chave do relato.
    """
    texto_processado = processar_texto(relato)
    palavras = texto_processado.split()
    # Retorna as palavras únicas mantendo a ordem de aparição
    vistas = set()
    palavras_chave = []
    for palavra in palavras:
        if palavra not in vistas:
            vistas.add(palavra)
            palavras_chave.append(palavra)
        if len(palavras_chave) >= top_n:
            break
    return palavras_chave
