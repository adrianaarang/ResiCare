from app.core.retry import generar_con_validacion, TriajeFallidoError
from app.providers.ollama_provider import OllamaProvider
from app.schemas.triaje import TriajeIncidencia

provider = OllamaProvider(modelo="llama3.2:3b")

try:
    resultado, intentos = generar_con_validacion(
        provider=provider,
        system_prompt="Eres un asistente de triaje en una residencia de ancianos. Devuelve SOLO un JSON.",
        user_prompt="Incidencia: mareo al levantarse. Residente con riesgo de caída alto.",
        esquema=TriajeIncidencia,
        max_intentos=3,
    )
    print(f"Validado en el intento {intentos}")
    print(resultado.model_dump_json(indent=2))
except TriajeFallidoError as e:
    print(f"Fallo tras {e.intentos} intentos: {e.ultimo_error}")