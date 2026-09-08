from pydantic import BaseModel, field_validator
from typing import Literal, Optional

Categoria = Literal[
    "clinica", "suministros_farmacia",
    "infraestructura_mantenimiento", "personal_organizacion"
]
Urgencia = Literal["critica", "alta", "media", "baja"]

DEPARTAMENTO_POR_CATEGORIA = {
    "clinica": "enfermeria",
    "suministros_farmacia": "farmacia",
    "infraestructura_mantenimiento": "mantenimiento",
    "personal_organizacion": "direccion_rrhh"
}

class TriajeIncidencia(BaseModel):
    residente_id: Optional[str] = None
    texto_original: str
    categoria: Categoria
    subcategoria: str
    urgencia: Urgencia
    resumen: str
    razonamiento: str

    @field_validator("resumen")
    @classmethod
    def resumen_max_10_palabras(cls, v: str) -> str:
        if len(v.split()) > 10:
            raise ValueError(f"El resumen tiene {len(v.split())} palabras, máximo 10")
        return v

    @property
    def departamento(self) -> str:
        return DEPARTAMENTO_POR_CATEGORIA[self.categoria]