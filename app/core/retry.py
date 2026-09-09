"""
Envuelve la llamada a un proveedor LLM (o al agente) con:
- Validación automática contra un esquema Pydantic
- Reintento con el error explicado al modelo si la validación falla
- Límite de intentos para no colapsar el servicio ante fallos repetidos
"""
from typing import Type, TypeVar, Callable
from pydantic import BaseModel, ValidationError

from app.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class TriajeFallidoError(Exception):
    """Se lanza cuando el modelo no logra devolver un formato válido
    tras agotar todos los reintentos permitidos."""
    def __init__(self, intentos: int, ultimo_error: str):
        self.intentos = intentos
        self.ultimo_error = ultimo_error
        super().__init__(
            f"El modelo no devolvió un formato válido tras {intentos} intentos. "
            f"Último error: {ultimo_error}"
        )


def generar_con_validacion(
    provider: LLMProvider,
    system_prompt: str,
    user_prompt: str,
    esquema: Type[T],
    max_intentos: int = 3,
) -> tuple[T, int]:
    """Versión para un provider simple (sin herramientas). Ver validar_con_reintento
    para la versión genérica que también sirve con el agente."""
    def llamar(system_prompt: str, user_prompt: str) -> str:
        respuesta = provider.generar(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=esquema.model_json_schema(),
        )
        return respuesta.contenido

    return validar_con_reintento(llamar, system_prompt, user_prompt, esquema, max_intentos)


def validar_con_reintento(
    funcion_generadora: Callable[[str, str], str],
    system_prompt: str,
    user_prompt: str,
    esquema: Type[T],
    max_intentos: int = 3,
) -> tuple[T, int]:
    """
    Versión genérica: recibe cualquier función que tome (system_prompt, user_prompt)
    y devuelva texto crudo. Sirve tanto para un provider simple como para el
    agente completo (ejecutar_agente), sin acoplarse a ninguno de los dos.
    """
    prompt_actual = user_prompt
    ultimo_error = ""

    for intento in range(1, max_intentos + 1):
        contenido = funcion_generadora(system_prompt, prompt_actual)

        try:
            objeto_validado = esquema.model_validate_json(contenido)
            return objeto_validado, intento
        except ValidationError as e:
            ultimo_error = str(e)
            prompt_actual = (
                f"{user_prompt}\n\n"
                f"Tu respuesta anterior no cumplía el formato requerido. "
                f"Error exacto:\n{ultimo_error}\n\n"
                f"Corrige tu respuesta y devuelve SOLO el JSON válido."
            )

    raise TriajeFallidoError(intentos=max_intentos, ultimo_error=ultimo_error)