"""
avaliacao/avaliar_sentence_transformers.py
============================================
Mede precisao, recall e F1 do classificador semantico
(ia/classificador_semantico.py) contra o mesmo dataset de teste
usado para o classificador de palavras-chave.

Nao altera nada do sistema em producao.

Uso:
    python avaliacao/avaliar_sentence_transformers.py
"""
import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.metrics import classification_report

from ia.classificador_semantico import classificador_semantico

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'dataset_teste.csv')
RESULTADOS_DIR = os.path.join(BASE_DIR, 'resultados')
NOME_CLASSIFICADOR = 'sentence-transformers'


def carregar_dataset():
    with open(DATASET_PATH, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def avaliar():
    casos = carregar_dataset()

    print("Carregando modelo (primeira vez pode demorar para baixar)...")
    y_true = []
    y_pred = []
    erros = []

    for caso in casos:
        resultado = classificador_semantico.analisar(caso['relato'])
        sub_correta = caso['sub_area_correta']
        sub_prevista = resultado['sub_area']

        y_true.append(sub_correta)
        y_pred.append(sub_prevista)

        if sub_correta != sub_prevista:
            erros.append({
                'id': caso['id'],
                'relato': caso['relato'],
                'esperado': sub_correta,
                'previsto': sub_prevista,
                'dificuldade': caso['dificuldade'],
                'similaridade': resultado['similaridade'],
            })

    relatorio_dict = classification_report(y_true, y_pred, zero_division=0, output_dict=True)
    relatorio_texto = classification_report(y_true, y_pred, zero_division=0)

    print(f"\n=== Avaliacao: {NOME_CLASSIFICADOR} ===\n")
    print(relatorio_texto)
    print(f"Total de casos: {len(casos)}")
    print(f"Acertos: {len(casos) - len(erros)} | Erros: {len(erros)} ({len(erros) / len(casos) * 100:.1f}%)\n")

    print("--- Erros por dificuldade ---")
    contagem_dificuldade = Counter(e['dificuldade'] for e in erros)
    for dif in ('facil', 'medio', 'dificil'):
        print(f"{dif}: {contagem_dificuldade.get(dif, 0)} erro(s)")

    if erros:
        print("\n--- Detalhe dos erros ---")
        for e in erros:
            print(f"[{e['id']}] ({e['dificuldade']}, sim={e['similaridade']:.2f}) \"{e['relato']}\"")
            print(f"      esperado: {e['esperado']} | previsto: {e['previsto']}")

    os.makedirs(RESULTADOS_DIR, exist_ok=True)
    saida = {
        'classificador': NOME_CLASSIFICADOR,
        'data': datetime.now().isoformat(),
        'total_casos': len(casos),
        'total_erros': len(erros),
        'relatorio': relatorio_dict,
        'erros': erros,
    }
    caminho_saida = os.path.join(RESULTADOS_DIR, 'resultado_sentence_transformers.json')
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"\nResultado salvo em: {caminho_saida}")


if __name__ == '__main__':
    avaliar()
