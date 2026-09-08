from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
from app.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)

class TriajeFallidoError(Exception):
    def __init__(self, intentos: int, ultimo_error: str):
        self.intentos = intentos
        self.ultimo_error = ultimo_error
        super().__init__(f"El modelo no devolvió un formato válido tras {intentos} intentos.")

def generar_con_validacion(
    provider: LLMProvider,
    system_prompt: str,
    user_prompt: str,
    esquema: Type[T],
    max_intentos: int = 3,
) -> tuple[T, int]:
    prompt_actual = user_prompt
    ultimo_error = ""

    for intento in range(1, max_intentos + 1):
        respuesta = provider.generar(
            system_prompt=system_prompt,
            user_prompt=prompt_actual,
            json_schema=esquema.model_json_schema(),
        )
        try:
            return esquema.model_validate_json(respuesta.contenido), intento
        except ValidationError as e:
            ultimo_error = str(e)
            prompt_actual = (
                f"{user_prompt}\n\nTu respuesta anterior no cumplía el formato requerido. "
                f"Error exacto:\n{ultimo_error}\n\nCorrige tu respuesta y devuelve SOLO el JSON válido."
            )

    raise TriajeFallidoError(intentos=max_intentos, ultimo_error=ultimo_error)