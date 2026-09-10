"""
Vector store (ChromaDB) sobre el histÃ³rico de incidencias, para detectar
reincidencia: incidencias pasadas semÃ¡nticamente parecidas a una nueva,
opcionalmente filtradas por residente.
"""
import json
from pathlib import Path

import chromadb

from app.rag.embeddings import obtener_embedding

RUTA_HISTORICO = Path(__file__).parent.parent.parent / "data" / "incidencias_historico.json"
RUTA_DB = Path(__file__).parent.parent.parent / "data" / "chroma_db"

_cliente = chromadb.PersistentClient(path=str(RUTA_DB))
_coleccion = _cliente.get_or_create_collection(name="incidencias_historico", metadata={"hnsw:space": "cosine"})


def indexar_historico(forzar: bool = False) -> int:
    """
    Carga data/incidencias_historico.json y lo indexa en ChromaDB.
    Si ya hay datos indexados y forzar=False, no hace nada (evita duplicar).
    Devuelve el nÃºmero de incidencias indexadas.
    """
    global _coleccion

    if _coleccion.count() > 0 and not forzar:
        return _coleccion.count()

    if forzar:
        # Chroma no tiene "vaciar colecciÃ³n" directo; recreamos
        _cliente.delete_collection("incidencias_historico")
        _coleccion = _cliente.get_or_create_collection(name="incidencias_historico", metadata={"hnsw:space": "cosine"})

    with open(RUTA_HISTORICO, "r", encoding="utf-8") as f:
        historico = json.load(f)

    for entrada in historico:
        embedding = obtener_embedding(entrada["texto"])
        _coleccion.add(
            ids=[entrada["id"]],
            embeddings=[embedding],
            documents=[entrada["texto"]],
            metadatas=[{
                "residente_id": entrada.get("residente_id") or "",
                "categoria": entrada.get("categoria", ""),
                "urgencia": entrada.get("urgencia", ""),
                "fecha": entrada.get("fecha", ""),
            }],
        )

    return _coleccion.count()


def buscar_incidencias_similares(texto: str, residente_id: str | None = None, top_k: int = 3) -> str:
    """
    Busca en el histÃ³rico incidencias semÃ¡nticamente parecidas al texto dado.
    Si se pasa residente_id, filtra para buscar solo dentro de las de ese residente
    (que es justo el caso de uso de reincidencia).

    Devuelve un JSON (string) con la lista de coincidencias, para que encaje
    igual que el resto de herramientas del agente.
    """
    embedding_consulta = obtener_embedding(texto)

    filtro = {"residente_id": residente_id} if residente_id else None

    resultados = _coleccion.query(
        query_embeddings=[embedding_consulta],
        n_results=top_k,
        where=filtro,
    )

    coincidencias = []
    documentos = resultados["documents"][0] if resultados["documents"] else []
    metadatas = resultados["metadatas"][0] if resultados["metadatas"] else []
    distancias = resultados["distances"][0] if resultados["distances"] else []

    for doc, meta, dist in zip(documentos, metadatas, distancias):
        coincidencias.append({
            "texto": doc,
            "fecha": meta.get("fecha"),
            "urgencia_asignada": meta.get("urgencia"),
            "similitud": round(1 - dist, 3),  # convertimos distancia a "similitud" (mÃ¡s alto = mÃ¡s parecido)
        })

    return json.dumps({"incidencias_similares_encontradas": len(coincidencias), "resultados": coincidencias})


# Esquema para que el agente pueda invocar esta funciÃ³n como herramienta
TOOL_BUSCAR_INCIDENCIAS_SIMILARES = {
    "type": "function",
    "function": {
        "name": "buscar_incidencias_similares",
        "description": (
            "Busca en el histÃ³rico de incidencias pasadas casos semÃ¡nticamente "
            "parecidos al texto actual, para detectar reincidencia. Ãšsala cuando "
            "quieras comprobar si un residente ha tenido sÃ­ntomas similares "
            "recientemente, ya que la repeticiÃ³n puede justificar subir la urgencia."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "texto": {"type": "string", "description": "El texto de la incidencia actual"},
                "residente_id": {
                    "type": "string",
                    "description": "Id del residente, para limitar la bÃºsqueda a su propio historial"
                }
            },
            "required": ["texto"]
        }
    }
}
