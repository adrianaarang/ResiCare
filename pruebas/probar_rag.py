from app.rag.vectorstore import indexar_historico, buscar_incidencias_similares

n = indexar_historico(forzar=True)
print(f"Indexadas {n} incidencias")

resultado = buscar_incidencias_similares(
    texto="El residente de la 204 dice sentirse mareado al levantarse de la silla",
    residente_id="res-204"
)
print(resultado)