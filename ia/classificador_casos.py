def classificar_caso(relato: str) -> str:
    global _modelo_treinado
    try:
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
