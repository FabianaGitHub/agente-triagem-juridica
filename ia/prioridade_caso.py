"""
ia/prioridade_caso.py
=====================
Módulo de Cálculo de Prioridade do Caso

Este módulo implementa um sistema baseado em regras (rule-based system)
para determinar o nível de urgência de um caso jurídico. A abordagem
baseada em regras é uma técnica clássica de IA que utiliza conhecimento
especializado codificado explicitamente para tomar decisões.

A prioridade é calculada com base na presença de palavras-chave no relato
do cliente, seguindo critérios definidos por especialistas jurídicos:

    - Prioridade 1 — URGENTE: situações de risco imediato à integridade
      física, liberdade ou moradia do cliente.
    - Prioridade 2 — ALTA: situações com impacto financeiro significativo
      ou que exigem ação rápida para evitar maiores danos.
    - Prioridade 3 — NORMAL: demais casos que seguem o fluxo regular
      de atendimento jurídico.

Função principal:
    - calcular_prioridade(relato): analisa o texto e retorna a prioridade.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PALAVRAS_URGENTE, PALAVRAS_ALTA


# Palavras-chave expandidas para maior precisão na detecção de urgência
_PALAVRAS_URGENTE_EXPANDIDAS = PALAVRAS_URGENTE + [
    "despejo", "violência", "ameaça", "prisão", "hospital",
    "agressão", "morte", "falecimento", "urgente", "emergência",
    "sequestro", "estupro", "abuso", "tortura", "suicídio",
    "internação", "uti", "cirurgia", "acidente grave", "incêndio",
    "desabamento", "reintegração de posse", "liminar", "mandado",
]

_PALAVRAS_ALTA_EXPANDIDAS = PALAVRAS_ALTA + [
    "banco", "demissão", "cobrança", "negativação",
    "rescisão", "despejo", "execução", "penhora", "bloqueio",
    "dívida", "protesto", "inadimplência", "multa", "embargo",
    "suspensão", "cancelamento", "fraude", "golpe", "estelionato",
    "falência", "insolvência", "corte", "desligamento",
]


def calcular_prioridade(relato: str) -> str:
    # 1. Consulta o Agente (Motor de Decisão)
    from ia.motor_decisao import agente_decisao
    decisao = agente_decisao.analisar(relato)
    
    niveis = {1: "Prioridade 1 — URGENTE", 2: "Prioridade 2 — ALTA", 3: "Prioridade 3 — NORMAL"}

    if decisao["area"] != "Indefinida":
        return niveis.get(decisao["prioridade"], "Prioridade 3 — NORMAL")

    relato_lower = relato.lower()

    # Verifica prioridade URGENTE (nível mais alto)
    for palavra in _PALAVRAS_URGENTE_EXPANDIDAS:
        if palavra in relato_lower:
            return "Prioridade 1 — URGENTE"

    # Verifica prioridade ALTA
    for palavra in _PALAVRAS_ALTA_EXPANDIDAS:
        if palavra in relato_lower:
            return "Prioridade 2 — ALTA"

    # Caso padrão: prioridade NORMAL
    return "Prioridade 3 — NORMAL"


def obter_nivel_prioridade(prioridade_str: str) -> int:
    """
    Extrai o número do nível de prioridade a partir da string formatada.

    Parâmetros:
        prioridade_str (str): String de prioridade no formato padrão.

    Retorna:
        int: Número da prioridade (1, 2 ou 3).
    """
    if "1" in prioridade_str:
        return 1
    elif "2" in prioridade_str:
        return 2
    return 3


def obter_cor_prioridade(prioridade_str: str) -> str:
    """
    Retorna a cor associada ao nível de prioridade para uso na interface.

    Parâmetros:
        prioridade_str (str): String de prioridade no formato padrão.

    Retorna:
        str: Código hexadecimal da cor correspondente ao nível.
    """
    nivel = obter_nivel_prioridade(prioridade_str)
    cores = {
        1: "#e74c3c",   # Vermelho — URGENTE
        2: "#e67e22",   # Laranja — ALTA
        3: "#27ae60",   # Verde — NORMAL
    }
    return cores.get(nivel, "#27ae60")


def listar_palavras_gatilho(relato: str) -> dict:
    """
    Identifica quais palavras-gatilho foram encontradas no relato.

    Útil para fins de auditoria e explicabilidade da decisão de prioridade.

    Parâmetros:
        relato (str): Texto bruto do relato jurídico.

    Retorna:
        dict: Dicionário com as palavras encontradas por nível de prioridade.
              Exemplo: {"urgente": ["violência"], "alta": ["demissão"]}
    """
    relato_lower = relato.lower()

    encontradas_urgente = [
        p for p in _PALAVRAS_URGENTE_EXPANDIDAS if p in relato_lower
    ]
    encontradas_alta = [
        p for p in _PALAVRAS_ALTA_EXPANDIDAS if p in relato_lower
    ]

    return {
        "urgente": encontradas_urgente,
        "alta": encontradas_alta,
    }
