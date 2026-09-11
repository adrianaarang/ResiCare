"""
Persistencia del Libro de Incidencias en SQLite.
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from app.schemas.triaje import TriajeIncidencia

RUTA_DB = Path(__file__).parent.parent.parent / "data" / "libro_incidencias.db"


def _conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(RUTA_DB)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db() -> None:
    with _conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                fecha_incidente TEXT NOT NULL,
                turno TEXT NOT NULL,
                residente_id TEXT,
                texto_original TEXT NOT NULL,
                categoria TEXT NOT NULL,
                urgencia TEXT NOT NULL,
                resumen TEXT NOT NULL,
                razonamiento TEXT NOT NULL,
                proveedor TEXT NOT NULL,
                es_reincidencia INTEGER NOT NULL DEFAULT 0,
                fecha_reincidencia_previa TEXT,
                casos_reincidencia_json TEXT
            )
        """)


def guardar_incidencia(
    incidencia: TriajeIncidencia,
    proveedor: str,
    turno: str,
    fecha_incidente: Optional[str] = None,
    es_reincidencia: bool = False,
    fecha_reincidencia_previa: Optional[str] = None,
    casos_reincidencia_json: Optional[str] = None,
) -> tuple[int, str]:
    fecha_iso = datetime.now(timezone.utc).isoformat()
    fecha_incidente = fecha_incidente or datetime.now(timezone.utc).date().isoformat()

    with _conectar() as conn:
        cursor = conn.execute(
            """INSERT INTO incidencias
               (fecha, fecha_incidente, turno, residente_id, texto_original,
                categoria, urgencia, resumen, razonamiento, proveedor,
                es_reincidencia, fecha_reincidencia_previa, casos_reincidencia_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                fecha_iso,
                fecha_incidente,
                turno,
                incidencia.residente_id,
                incidencia.texto_original,
                incidencia.categoria,
                incidencia.urgencia,
                incidencia.resumen,
                incidencia.razonamiento,
                proveedor,
                1 if es_reincidencia else 0,
                fecha_reincidencia_previa,
                casos_reincidencia_json,
            ),
        )
        return cursor.lastrowid, fecha_iso


def listar_incidencias(residente_id: Optional[str] = None, limite: int = 100) -> list[dict]:
    with _conectar() as conn:
        if residente_id:
            filas = conn.execute(
                "SELECT * FROM incidencias WHERE residente_id = ? ORDER BY fecha DESC LIMIT ?",
                (residente_id, limite),
            ).fetchall()
        else:
            filas = conn.execute(
                "SELECT * FROM incidencias ORDER BY fecha DESC LIMIT ?", (limite,)
            ).fetchall()
        return [dict(fila) for fila in filas]