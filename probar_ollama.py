from app.providers.ollama_provider import OllamaProvider
from app.schemas.triaje import TriajeIncidencia

provider = OllamaProvider(modelo="llama3.2:3b")

resp = provider.generar(
    system_prompt=(
        "Eres un asistente de triaje en una residencia de ancianos. "
        "Devuelve SOLO un JSON con: categoria, subcategoria, urgencia, resumen, razonamiento."
    ),
    user_prompt=(
        "Incidencia: el residente de la 204 dice sentirse mareado al levantarse. "
        "Tiene un flag de riesgo de caída alto activo."
    ),
    json_schema=TriajeIncidencia.model_json_schema(),
)

print("--- Respuesta cruda de Ollama ---")
print(resp.model_dump_json(indent=2))

print("\n--- Validando contra el esquema Pydantic ---")
incidencia = TriajeIncidencia.model_validate_json(resp.contenido)
print(incidencia.model_dump_json(indent=2))
print("Departamento derivado:", incidencia.departamento)