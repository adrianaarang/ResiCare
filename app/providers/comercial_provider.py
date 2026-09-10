"""
Proveedor comercial vía Groq (API externa, pago por uso con nivel gratuito).

Requiere una API key gratuita de https://console.groq.com/keys,
disponible como variable de entorno GROQ_API_KEY.

Nota sobre el modelo: usamos "openai/gpt-oss-120b" (120B parámetros),
bastante más grande que el llama3.2:3b que corres en local con Ollama.
Esto es intencional para la comparación: no solo contrastamos coste/latencia,
sino también la diferencia de calidad entre un modelo pequeño local y uno
grande servido en la nube.

(Nota histórica: usábamos llama-3.3-70b-versatile, pero Groq lo retiró
el 16 de agosto de 2026. Si en el futuro este modelo también se retira,
revisa console.groq.com/docs/deprecations para el reemplazo recomendado.)
"""
import os
import time
from typing import Optional

from app.providers.base import LLMProvider, ProviderResponse
from app.core.http_retry import post_con_backoff

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Precios aproximados por millón de tokens (verificar cifras actuales en
# console.groq.com/docs/models, ya que Groq las actualiza con frecuencia)
PRECIO_INPUT_POR_MILLON = 0.15
PRECIO_OUTPUT_POR_MILLON = 0.60


class GroqProvider(LLMProvider):
    def __init__(self, modelo: str = "openai/gpt-oss-120b", api_key: Optional[str] = None):
        self.modelo = modelo
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Falta la API key de Groq. Define la variable de entorno GROQ_API_KEY "
                "o pásala explícitamente al crear GroqProvider(api_key=...)."
            )

    def generar(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[dict] = None,
    ) -> ProviderResponse:
        # Nota: usamos JSON mode simple ("json_object"), no el structured-output
        # estricto de Groq (json_schema con strict=True), porque este último exige
        # que TODOS los campos sean obligatorios y no admite bien los campos
        # opcionales de nuestro esquema (residente_id). La validación estricta
        # real la seguimos haciendo con Pydantic en core/retry.py, igual que con Ollama.
        payload = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        inicio = time.perf_counter()
        respuesta = post_con_backoff(
            GROQ_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json_payload=payload,
            timeout=60,
        )
        latencia_ms = (time.perf_counter() - inicio) * 1000

        data = respuesta.json()
        contenido = data["choices"][0]["message"]["content"]
        uso = data.get("usage", {})
        tokens_entrada = uso.get("prompt_tokens", 0)
        tokens_salida = uso.get("completion_tokens", 0)

        coste = (
            tokens_entrada / 1_000_000 * PRECIO_INPUT_POR_MILLON
            + tokens_salida / 1_000_000 * PRECIO_OUTPUT_POR_MILLON
        )

        return ProviderResponse(
            contenido=contenido,
            proveedor="groq",
            modelo=self.modelo,
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
            latencia_ms=round(latencia_ms, 1),
            coste_usd=round(coste, 6),
        )