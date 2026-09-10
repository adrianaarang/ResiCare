import requests

OLLAMA_EMBEDDINGS_URL = "http://localhost:11434/api/embeddings"
MODELO_EMBEDDING = "nomic-embed-text"


def obtener_embedding(texto):
    respuesta = requests.post(
        OLLAMA_EMBEDDINGS_URL,
        json={"model": MODELO_EMBEDDING, "prompt": texto},
        timeout=30,
    )
    respuesta.raise_for_status()
    return respuesta.json()["embedding"]
