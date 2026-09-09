"""
Herramientas que el agente puede invocar durante su ciclo ReAct.

Cada herramienta tiene:
- Una función Python real que la ejecuta
- Un esquema (formato OpenAI-style, que Ollama y la mayoría de proveedores
  comerciales entienden) que se le pasa al modelo para que sepa que existe
"""
import json
from pathlib import Path
from app.schemas.residente import Residente

RUTA_RESIDENTES = Path(__file__).parent.parent.parent / "data" / "residentes.json"


def _cargar_residentes() -> dict:
    with open(RUTA_RESIDENTES, "r", encoding="utf-8") as f:
        return json.load(f)


def consultar_residente(residente_id: str) -> str:
    """Devuelve el contexto clínico (flags, condiciones) de un residente, en JSON."""
    residentes = _cargar_residentes()
    datos = residentes.get(residente_id)
    if datos is None:
        return json.dumps({"error": f"No existe ningún residente con id '{residente_id}'"})
    residente = Residente(**datos)
    return residente.model_dump_json()


# Esquema que se le presenta al modelo para que sepa cómo invocar la herramienta
TOOL_CONSULTAR_RESIDENTE = {
    "type": "function",
    "function": {
        "name": "consultar_residente",
        "description": (
            "Consulta el contexto clínico de un residente (flags de riesgo activos, "
            "deterioro cognitivo, condiciones crónicas) a partir de su identificador. "
            "Úsala SIEMPRE que la incidencia mencione a un residente concreto, antes "
            "de decidir la urgencia."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "residente_id": {
                    "type": "string",
                    "description": "Identificador del residente, ej. 'res-204'"
                }
            },
            "required": ["residente_id"]
        }
    }
}

# Registro de nombre -> función ejecutable, para que el orquestador
# sepa qué código correr cuando el modelo pide una herramienta
HERRAMIENTAS_DISPONIBLES = {
    "consultar_residente": consultar_residente,
}
