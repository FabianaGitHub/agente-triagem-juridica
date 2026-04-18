"""
config.py
=========
Módulo de configurações globais do sistema.

Este arquivo centraliza todas as configurações do projeto, como caminhos de
arquivos, nome do banco de dados e outras constantes utilizadas pelos demais
módulos. Ao centralizar as configurações aqui, facilita-se a manutenção e
a portabilidade do sistema.
"""

import os

# Diretório raiz do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho para o banco de dados SQLite
BANCO_DIR = os.path.join(BASE_DIR, "banco")
BANCO_PATH = os.path.join(BANCO_DIR, "triagem_juridica.db")

# Caminho para os dados de treinamento do modelo de IA
DADOS_DIR = os.path.join(BASE_DIR, "dados")
DATASET_PATH = os.path.join(DADOS_DIR, "treinamento_casos.csv")

# Caminho para salvar os relatórios PDF gerados
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios", "pdfs_gerados")
os.makedirs(RELATORIOS_DIR, exist_ok=True)

# Caminho para salvar os arquivos de anexo (evidências)
ANEXOS_DIR = os.path.join(BASE_DIR, "dados", "anexos_casos")
os.makedirs(ANEXOS_DIR, exist_ok=True)

# Nome do modelo spaCy utilizado para NLP em português
SPACY_MODEL = "pt_core_news_sm"

# Categorias jurídicas reconhecidas pelo classificador
CATEGORIAS_JURIDICAS = [
    "Direito do Consumidor",
    "Direito Trabalhista",
    "Direito de Família",
    "Direito Bancário",
]

# Palavras-chave para cálculo de prioridade
PALAVRAS_URGENTE = ["despejo", "violência", "ameaça", "prisão", "hospital"]
PALAVRAS_ALTA = ["banco", "demissão", "cobrança", "negativação"]

# Configurações de aparência da interface gráfica
COR_FUNDO = "#f0f4f8"
COR_PRIMARIA = "#1a3c5e"
COR_SECUNDARIA = "#2980b9"
COR_URGENTE = "#e74c3c"
COR_ALTA = "#e67e22"
COR_NORMAL = "#27ae60"
FONTE_TITULO = ("Helvetica", 16, "bold")
FONTE_LABEL = ("Helvetica", 10)
FONTE_BOTAO = ("Helvetica", 10, "bold")
