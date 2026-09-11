"""
Esquema de salida del LLM para el Libro de Incidencias de Enfermeria.

Alcance recortado a solo incidencias clinicas (decision de producto:
ResiCare se centra en el libro de novedades de enfermeria, no en
incidencias de infraestructura/farmacia/personal en general).
"""
from pydantic import BaseModel, field_validator
from typing import Literal, Optional

Categoria = Literal["caida", "alteracion_estado", "medicacion", "constantes_vitales"]
Urgencia = Literal["critica", "alta", "media", "baja"]


class TriajeIncidencia(BaseModel):
    residente_id: Optional[str] = None
    texto_original: str
    categoria: Categoria
    urgencia: Urgencia
    resumen: str
    razonamiento: str

    @field_validator("resumen")
    @classmethod
    def resumen_no_vacio_y_max_10_palabras(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El resumen no puede estar vacio")
        if len(v.split()) > 10:
            raise ValueError(f"El resumen tiene {len(v.split())} palabras, maximo 10")
        return v

    @property
    def departamento(self) -> str:
        return "enfermeria"
