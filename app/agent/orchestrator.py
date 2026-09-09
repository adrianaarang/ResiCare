"""
Orquestador del ciclo ReAct: el modelo puede llamar a herramientas
(Action) y recibir sus resultados (Observation) antes de dar la
respuesta final, en vez de recibir todo el contexto ya masticado
en el prompt.
"""
import inspect
import json
import requests
from typing import Callable

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


def _filtrar_argumentos_validos(funcion: Callable, argumentos: dict) -> dict:
    parametros_validos = inspect.signature(funcion).parameters
    return {k: v for k, v in argumentos.items() if k in parametros_validos}


def _ejecutar_herramienta_segura(funcion: Callable, argumentos: dict) -> str:
    try:
        argumentos_filtrados = _filtrar_argumentos_validos(funcion, argumentos)
        return funcion(**argumentos_filtrados)
    except TypeError as e:
        return json.dumps({"error": f"Argumentos invalidos al llamar a la herramienta: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Fallo inesperado al ejecutar la herramienta: {str(e)}"})


def ejecutar_agente(
    modelo: str,
    system_prompt: str,
    user_prompt: str,
    herramientas: list[dict],
    ejecutores: dict[str, Callable],
    json_schema: dict | None = None,
    max_turnos: int = 5,
) -> str:
    mensajes = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for turno in range(max_turnos):
        payload = {
            "model": modelo,
            "messages": mensajes,
            "tools": herramientas,
            "stream": False,
        }
        if json_schema:
            payload["format"] = json_schema

        respuesta = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=60)
        respuesta.raise_for_status()
        data = respuesta.json()
        mensaje_modelo = data["message"]
        mensajes.append(mensaje_modelo)

        tool_calls = mensaje_modelo.get("tool_calls")

        if not tool_calls:
            return mensaje_modelo["content"]

        for llamada in tool_calls:
            nombre_funcion = llamada["function"]["name"]
            argumentos = llamada["function"]["arguments"]

            funcion = ejecutores.get(nombre_funcion)
            if funcion is None:
                resultado = json.dumps({"error": f"Herramienta desconocida: {nombre_funcion}"})
            else:
                resultado = _ejecutar_herramienta_segura(funcion, argumentos)

            mensajes.append({"role": "tool", "content": resultado})

    raise RuntimeError(f"El agente no llego a una respuesta final tras {max_turnos} turnos")
