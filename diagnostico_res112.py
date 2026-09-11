from app.rag.vectorstore import buscar_incidencias_similares
import json

resultado = buscar_incidencias_similares(
    texto="Le duele la cabeza",
    residente_id="res-112"
)
print(json.dumps(json.loads(resultado), indent=2, ensure_ascii=False))