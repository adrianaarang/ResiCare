from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class ProviderResponse(BaseModel):
    contenido: str
    proveedor: str
    modelo: str
    tokens_entrada: int
    tokens_salida: int
    latencia_ms: float
    coste_usd: float

class LLMProvider(ABC):
    @abstractmethod
    def generar(self, system_prompt: str, user_prompt: str, json_schema: Optional[dict] = None) -> ProviderResponse:
        raise NotImplementedError