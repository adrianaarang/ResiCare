from dotenv import load_dotenv
load_dotenv()

from app.providers.comercial_provider import GroqProvider
from app.agent.prompts import SYSTEM_PROMPT

provider = GroqProvider()

resp = provider.generar(
    system_prompt=SYSTEM_PROMPT,
    user_prompt="Incidencia: El residente de la 204 dice sentirse mareado al levantarse de la silla. Tiene un flag de riesgo de caída alto activo.",
)

print("--- Contenido crudo devuelto por Groq ---")
print(resp.contenido)