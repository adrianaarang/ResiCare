from dotenv import load_dotenv
load_dotenv()

from app.agent.orchestrator import ejecutar_agente
from app.agent.tools import TOOL_CONSULTAR_RESIDENTE, HERRAMIENTAS_DISPONIBLES
from app.rag.vectorstore import TOOL_BUSCAR_INCIDENCIAS_SIMILARES, buscar_incidencias_similares, indexar_historico
from app.agent.prompts import SYSTEM_PROMPT
from app.schemas.triaje import TriajeIncidencia
from app.core.retry import validar_con_reintento, TriajeFallidoError

indexar_historico()

HERRAMIENTAS = [TOOL_CONSULTAR_RESIDENTE, TOOL_BUSCAR_INCIDENCIAS_SIMILARES]
EJECUTORES = {
    **HERRAMIENTAS_DISPONIBLES,
    "buscar_incidencias_similares": buscar_incidencias_similares,
}

system_prompt_agente = SYSTEM_PROMPT + (
     "\n\nHERRAMIENTAS DISPONIBLES (uso obligatorio, no opcional):\n"
    "- Si el texto menciona un identificador de residente (ej. 'res-204'), DEBES llamar "
    "SIEMPRE a consultar_residente antes de responder, sin excepcion. No asumas que no "
    "hay flags activos sin haberlo consultado primero.\n"
    "- DEBES llamar tambien a buscar_incidencias_similares (con el texto y, si lo conoces, "
    "el residente_id) para comprobar reincidencia, antes de dar tu respuesta final. "
    "Si encuentras 2 o mas incidencias similares recientes del mismo residente, "
    "considera subir la urgencia y mencionalo explicitamente en tu razonamiento.\n"
    "No respondas con la clasificacion final hasta haber llamado a AMBAS herramientas "
    "cuando el texto incluya un id de residente."
)

def llamar_agente(system_prompt: str, user_prompt: str) -> str:
    return ejecutar_agente(
        modelo="llama3.2:3b",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        herramientas=HERRAMIENTAS,
        ejecutores=EJECUTORES,
        json_schema=TriajeIncidencia.model_json_schema(),
    )

try:
    incidencia, intentos = validar_con_reintento(
        funcion_generadora=llamar_agente,
        system_prompt=system_prompt_agente,
        user_prompt="Incidencia: El residente de la 204 (id: res-204) dice sentirse mareado al levantarse de la silla.",
        esquema=TriajeIncidencia,
        max_intentos=3,
    )
    print(f"Validado en el intento {intentos}")
    print(incidencia.model_dump_json(indent=2))
    print("Departamento derivado:", incidencia.departamento)
except TriajeFallidoError as e:
    print(f"Fallo tras {e.intentos} intentos: {e.ultimo_error}")