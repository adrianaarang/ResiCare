import json
import requests
from typing import Callable

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

def ejecutar_agente(modelo, system_prompt, user_prompt, herramientas, ejecutores, max_turnos=5):
    mensajes = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    for turno in range(max_turnos):
        respuesta = requests.post(OLLAMA_CHAT_URL, json={
            "model": modelo, "messages": mensajes,
            "tools": herramientas, "stream": False,
        }, timeout=60)
        respuesta.raise_for_status()
        data = respuesta.json()
        mensaje_modelo = data["message"]
        mensajes.append(mensaje_modelo)

        tool_calls = mensaje_modelo.get("tool_calls")
        if not tool_calls:
            return mensaje_modelo["content"]

        for llamada in tool_calls:
            nombre = llamada["function"]["name"]
            argumentos = llamada["function"]["arguments"]
            funcion = ejecutores.get(nombre)
            resultado = funcion(**argumentos) if funcion else json.dumps({"error": f"Herramienta desconocida: {nombre}"})
            mensajes.append({"role": "tool", "content": resultado})

    raise RuntimeError(f"El agente no llegó a una respuesta final tras {max_turnos} turnos")