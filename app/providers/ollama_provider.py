import time
from typing import Optional
import requests
from app.providers.base import LLMProvider, ProviderResponse

OLLAMA_URL = "http://localhost:11434/api/generate"

class OllamaProvider(LLMProvider):
    def __init__(self, modelo: str = "llama3.2:3b"):
        self.modelo = modelo

    def generar(self, system_prompt, user_prompt, json_schema=None) -> ProviderResponse:
        prompt_completo = f"{system_prompt}\n\n{user_prompt}"
        payload = {
            "model": self.modelo,
            "prompt": prompt_completo,
            "stream": False,
            "format": json_schema if json_schema else "json",
        }
        inicio = time.perf_counter()
        respuesta = requests.post(OLLAMA_URL, json=payload, timeout=60)
        respuesta.raise_for_status()
        latencia_ms = (time.perf_counter() - inicio) * 1000
        data = respuesta.json()
        return ProviderResponse(
            contenido=data["response"],
            proveedor="ollama",
            modelo=self.modelo,
            tokens_entrada=data.get("prompt_eval_count", 0),
            tokens_salida=data.get("eval_count", 0),
            latencia_ms=round(latencia_ms, 1),
            coste_usd=0.0,
        )
