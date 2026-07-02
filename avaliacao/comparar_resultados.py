"""
avaliacao/comparar_resultados.py
==================================
Le todos os resultados salvos em avaliacao/resultados/*.json
(um arquivo por classificador avaliado) e gera:

  - tabela_comparativa.csv  -> abre direto no Excel, pronta pro TCC
  - grafico_comparativo.png -> precisao/recall/F1 macro por classificador

Funciona com 1 classificador avaliado (mostra so a tabela dele) e
escala automaticamente conforme novos resultados forem adicionados
(ex: resultado_sentence_transformers.json).

Uso:
    python avaliacao/comparar_resultados.py
"""
import csv
import glob
import json
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTADOS_DIR = os.path.join(BASE_DIR, 'resultados')
TABELA_CSV = os.path.join(RESULTADOS_DIR, 'tabela_comparativa.csv')
GRAFICO_PNG = os.path.join(RESULTADOS_DIR, 'grafico_comparativo.png')


def carregar_resultados():
    arquivos = sorted(glob.glob(os.path.join(RESULTADOS_DIR, 'resultado_*.json')))
    resultados = []
    for caminho in arquivos:
        with open(caminho, encoding='utf-8') as f:
            resultados.append(json.load(f))
    return resultados


def montar_tabela(resultados):
    linhas = []
    for r in resultados:
        rel = r['relatorio']
        macro = rel['macro avg']
        linhas.append({
            'classificador': r['classificador'],
            'data': r['data'],
            'total_casos': r['total_casos'],
            'total_erros': r['total_erros'],
            'acuracia': round(rel['accuracy'], 4),
            'precisao_macro': round(macro['precision'], 4),
            'recall_macro': round(macro['recall'], 4),
            'f1_macro': round(macro['f1-score'], 4),
        })
    return linhas


def salvar_csv(linhas):
    with open(TABELA_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        writer.writeheader()
        writer.writerows(linhas)
    print(f"Tabela salva em: {TABELA_CSV}")


def gerar_grafico(linhas):
    classificadores = [l['classificador'] for l in linhas]
    metricas = ['precisao_macro', 'recall_macro', 'f1_macro']
    labels_metricas = ['Precisão', 'Recall', 'F1-score']

    x = range(len(classificadores))
    largura = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (metrica, label) in enumerate(zip(metricas, labels_metricas)):
        valores = [l[metrica] for l in linhas]
        posicoes = [pos + i * largura for pos in x]
        barras = ax.bar(posicoes, valores, largura, label=label)
        ax.bar_label(barras, fmt='%.2f', padding=2, fontsize=8)

    ax.set_ylabel('Score')
    ax.set_ylim(0, 1.05)
    ax.set_title('Comparação de classificadores — Triagem Jurídica ACESSUS')
    ax.set_xticks([pos + largura for pos in x])
    ax.set_xticklabels(classificadores)
    ax.legend()
    fig.tight_layout()
    fig.savefig(GRAFICO_PNG, dpi=150)
    print(f"Gráfico salvo em: {GRAFICO_PNG}")


def imprimir_tabela(linhas):
    print("\n=== Tabela comparativa ===")
    cabecalho = f"{'Classificador':<25}{'Acurácia':>10}{'Precisão':>10}{'Recall':>10}{'F1':>10}{'Erros':>8}"
    print(cabecalho)
    print('-' * len(cabecalho))
    for l in linhas:
        print(f"{l['classificador']:<25}{l['acuracia']:>10.2f}{l['precisao_macro']:>10.2f}"
              f"{l['recall_macro']:>10.2f}{l['f1_macro']:>10.2f}{l['total_erros']:>8}")


def comparar():
    resultados = carregar_resultados()
    if not resultados:
        print(f"Nenhum resultado encontrado em {RESULTADOS_DIR}. "
              f"Rode avaliar_classificador.py primeiro.")
        return

    linhas = montar_tabela(resultados)
    imprimir_tabela(linhas)
    salvar_csv(linhas)
    gerar_grafico(linhas)

    if len(linhas) == 1:
        print("\nApenas 1 classificador avaliado ate agora. "
              "Quando o Sentence Transformers for implementado e avaliado, "
              "rode este script novamente para ver a comparação lado a lado.")


if __name__ == '__main__':
    comparar()
