from dotenv import load_dotenv
load_dotenv()

from app.providers.comercial_provider import GroqProvider
from app.agent.prompts import SYSTEM_PROMPT
from app.schemas.triaje import TriajeIncidencia
from app.core.retry import generar_con_validacion, TriajeFallidoError

provider = GroqProvider()

try:
    incidencia, intentos = generar_con_validacion(
        provider=provider,
        system_prompt=SYSTEM_PROMPT,
        user_prompt="Incidencia: El residente de la 204 dice sentirse mareado al levantarse de la silla. Tiene un flag de riesgo de caída alto activo.",
        esquema=TriajeIncidencia,
        max_intentos=3,
    )
    print(f"Validado en el intento {intentos}")
    print(incidencia.model_dump_json(indent=2))
except TriajeFallidoError as e:
    print(f"Fallo: {e.ultimo_error}")