from app.core.retry import generar_con_validacion, TriajeFallidoError
from app.providers.ollama_provider import OllamaProvider
from app.schemas.triaje import TriajeIncidencia
from app.schemas.residente import Residente, FlagResidente
from app.agent.prompts import SYSTEM_PROMPT, construir_user_prompt

# Residente A: mareo + flag de riesgo de caída activo (tu caso de prueba)
residente_a = Residente(
    id="res-204",
    habitacion="204",
    edad=87,
    deterioro_cognitivo="ninguno",
    flags=[FlagResidente(tipo="riesgo_caida", nivel="alto", descripcion="2 caídas en el último mes")],
    condiciones_cronicas=["hipertension", "osteoporosis"]
)

user_prompt = construir_user_prompt(
    "El residente de la 204 dice sentirse mareado al levantarse de la silla",
    residente_a
)

provider = OllamaProvider(modelo="llama3.2:3b")

try:
    resultado, intentos = generar_con_validacion(
        provider=provider,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        esquema=TriajeIncidencia,
        max_intentos=3,
    )
    print(f"Validado en el intento {intentos}")
    print(resultado.model_dump_json(indent=2))
    print("Departamento derivado:", resultado.departamento)
except TriajeFallidoError as e:
    print(f"Fallo tras {e.intentos} intentos: {e.ultimo_error}")