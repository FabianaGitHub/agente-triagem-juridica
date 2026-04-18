"""
main.py
=======
Arquivo Principal — Sistema Inteligente de Triagem Jurídica com IA

Este é o ponto de entrada do sistema. Ao ser executado, ele:
    1. Inicializa o banco de dados SQLite (cria tabelas se não existirem)
    2. Treina o modelo de classificação de IA em background
    3. Inicia a interface gráfica principal (Tkinter)

Para executar o sistema:
    python main.py

Requisitos de instalação:
    pip install spacy scikit-learn fpdf2
    python -m spacy download pt_core_news_sm

Autor: Sistema desenvolvido para TCC — Projeto de Triagem Jurídica com IA
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk  # Adicione esta linha se não houver


def verificar_dependencias() -> bool:
    """
    Verifica se as bibliotecas essenciais estão instaladas.

    Retorna:
        bool: True se todas as dependências críticas estiverem disponíveis.
    """
    dependencias = {
        "sklearn": "scikit-learn",
        "fpdf": "fpdf2",
    }

    faltando = []
    for modulo, pacote in dependencias.items():
        try:
            __import__(modulo)
        except ImportError:
            faltando.append(pacote)

    if faltando:
        print("\n[AVISO] As seguintes bibliotecas não estão instaladas:")
        for pkg in faltando:
            print(f"  - {pkg}")
        print("\nInstale com o comando:")
        print(f"  pip install {' '.join(faltando)}")
        print("\nO sistema tentará iniciar mesmo assim com funcionalidades reduzidas.\n")
        return False

    return True


def inicializar_sistema():
    """
    Realiza todas as inicializações necessárias antes de abrir a interface.

    Etapas:
        1. Verifica dependências instaladas.
        2. Cria o banco de dados e as tabelas (se não existirem).
        3. Verifica a existência do dataset de treinamento.
    """
    print("=" * 60)
    print("  Sistema Inteligente de Triagem Jurídica com IA")
    print("  Inicializando...")
    print("=" * 60)

    # Verifica dependências
    verificar_dependencias()

    # Inicializa o banco de dados
    try:
        from banco.banco_dados import criar_banco
        criar_banco()
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar banco de dados: {e}")
        sys.exit(1)

    # Verifica dataset de treinamento
    from config import DATASET_PATH
    if not os.path.exists(DATASET_PATH):
        print(f"[AVISO] Dataset não encontrado em: {DATASET_PATH}")
        print("  O classificador usará o modo de fallback por palavras-chave.")
    else:
        print(f"[OK] Dataset encontrado: {DATASET_PATH}")

    print("[OK] Sistema inicializado com sucesso.")
    print("=" * 60)


def iniciar_interface():
    from interface.interface_insercao import InterfaceInsercao
    from interface.interface_consulta import InterfaceConsulta
    from interface.interface_chatbot import InterfaceChatbot


    root = tk.Tk()
    root.title("Agente de Triagem Jurídica com IA")
    root.geometry("900x850")

    tab_control = ttk.Notebook(root)
    
    tab_chatbot = tk.Frame(tab_control, bg="#f0f4f8") 
    tab_insercao = tk.Frame(tab_control, bg="#f0f4f8")
    tab_consulta = tk.Frame(tab_control, bg="#f0f4f8")
    
    tab_control.add(tab_chatbot, text='  Atendimento via Chatbot  ') 
    tab_control.add(tab_insercao, text='  Novo Cadastro Manual  ')
    tab_control.add(tab_consulta, text='  Consultar Casos  ')
    tab_control.pack(expand=1, fill="both")

    InterfaceChatbot(tab_chatbot) # INICIALIZE O CHATBOT
    InterfaceInsercao(tab_insercao)
    InterfaceConsulta(tab_consulta)

    root.mainloop()



if __name__ == "__main__":
    # Garante que o diretório do projeto está no path do Python
    projeto_dir = os.path.dirname(os.path.abspath(__file__))
    if projeto_dir not in sys.path:
        sys.path.insert(0, projeto_dir)

    inicializar_sistema()
    iniciar_interface()
