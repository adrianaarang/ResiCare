"""
Configuracion compartida de los tests.

Dos parches activos durante toda la sesion de tests:
1. indexar_historico() no se ejecuta de verdad (no requiere Ollama corriendo).
2. La base de datos del Libro de Incidencias usa un archivo de PRUEBA
   separado (tests/test_libro_incidencias.db), para que ejecutar los
   tests nunca escriba en tu base de datos real (data/libro_incidencias.db).
"""
from pathlib import Path
from unittest.mock import patch

_RUTA_DB_TEST = Path(__file__).parent / "test_libro_incidencias.db"
if _RUTA_DB_TEST.exists():
    _RUTA_DB_TEST.unlink()

_patch_rag = patch("app.rag.vectorstore.indexar_historico", return_value=0)
_patch_db = patch("app.core.almacen.RUTA_DB", _RUTA_DB_TEST)

_patch_rag.start()
_patch_db.start()

import app.main  # noqa: F401