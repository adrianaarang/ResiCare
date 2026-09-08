from pydantic import BaseModel, Field
from typing import Literal, Optional

FlagTipo = Literal["riesgo_caida", "riesgo_fuga", "riesgo_broncoaspiracion", "riesgo_ulceras_presion"]

class FlagResidente(BaseModel):
    tipo: FlagTipo
    nivel: Literal["alto", "medio", "bajo"]
    descripcion: Optional[str] = None

class Residente(BaseModel):
    id: str
    habitacion: str
    edad: int = Field(ge=0, le=120)
    deterioro_cognitivo: Literal["ninguno", "leve", "moderado", "severo"]
    flags: list[FlagResidente] = Field(default_factory=list)
    condiciones_cronicas: list[str] = Field(default_factory=list)