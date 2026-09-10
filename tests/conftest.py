"""
Configuracion compartida de los tests.

Parcheamos indexar_historico() ANTES de importar app.main, para que los
tests no dependan de tener Ollama corriendo (que seria necesario para
generar embeddings si el indice de ChromaDB estuviera vacio). Los tests
no verifican el contenido real del RAG, asi que esto es seguro.
"""
from unittest.mock import patch

with patch("app.rag.vectorstore.indexar_historico", return_value=0):
    import app.main  # noqa: F401