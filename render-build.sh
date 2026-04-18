#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala as bibliotecas da lista
pip install -r requirements.txt

# Baixa o modelo de português do spaCy (essencial para o Agente)
python -m spacy download pt_core_news_sm
