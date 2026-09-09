from app.agent.orchestrator import ejecutar_agente
from app.agent.tools import TOOL_CONSULTAR_RESIDENTE, HERRAMIENTAS_DISPONIBLES
from app.agent.prompts import SYSTEM_PROMPT
from app.schemas.triaje import TriajeIncidencia
from app.core.retry import validar_con_reintento, TriajeFallidoError

system_prompt_agente = SYSTEM_PROMPT + (
    "\n\nSi el texto de la incidencia menciona un identificador de residente "
    "(ej. 'res-204'), usa la herramienta consultar_residente para obtener su "
    "contexto clinico ANTES de decidir la urgencia."
)

def llamar_agente(system_prompt: str, user_prompt: str) -> str:
    return ejecutar_agente(
        modelo="llama3.2:3b",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        herramientas=[TOOL_CONSULTAR_RESIDENTE],
        ejecutores=HERRAMIENTAS_DISPONIBLES,
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
