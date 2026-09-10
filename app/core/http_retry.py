"""
POST con reintento y backoff exponencial ante rate limits (429) o errores
transitorios del servidor (5xx) de un proveedor externo. Respeta el header
Retry-After si el proveedor lo envia; si no, usa backoff exponencial con jitter.

Esto es especifico de proveedores EXTERNOS (ej. Groq) - Ollama, al correr en
local, no tiene rate limiting real que gestionar.
"""
import random
import time

import requests


class RateLimitAgotadoError(Exception):
    """Se lanza cuando se agotan los reintentos ante rate limiting persistente."""
    def __init__(self, intentos: int, ultimo_status: int):
        self.intentos = intentos
        self.ultimo_status = ultimo_status
        super().__init__(
            f"Rate limit persistente tras {intentos} intentos (ultimo status: {ultimo_status})"
        )


def post_con_backoff(
    url: str,
    headers: dict,
    json_payload: dict,
    timeout: int = 60,
    max_reintentos: int = 5,
    espera_base_segundos: float = 1.0,
) -> requests.Response:
    """
    Igual que requests.post, pero si el proveedor devuelve 429 (rate limit)
    o un 5xx (error transitorio del servidor), reintenta con backoff
    exponencial en vez de fallar inmediatamente.
    """
    ultima_respuesta = None

    for intento in range(1, max_reintentos + 1):
        respuesta = requests.post(url, headers=headers, json=json_payload, timeout=timeout)
        ultima_respuesta = respuesta

        if respuesta.status_code == 429 or respuesta.status_code >= 500:
            if intento == max_reintentos:
                break

            retry_after = respuesta.headers.get("Retry-After")
            if retry_after:
                espera = float(retry_after)
            else:
                espera = espera_base_segundos * (2 ** (intento - 1)) + random.uniform(0, 0.5)

            time.sleep(espera)
            continue

        respuesta.raise_for_status()
        return respuesta

    raise RateLimitAgotadoError(intentos=max_reintentos, ultimo_status=ultima_respuesta.status_code)
