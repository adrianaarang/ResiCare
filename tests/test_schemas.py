"""
Tests del esquema Pydantic TriajeIncidencia (alcance clinico) y las
alucinaciones estructurales que ya vimos en la practica.
"""
import pytest
from pydantic import ValidationError

from app.schemas.triaje import TriajeIncidencia


def test_incidencia_valida_se_acepta():
    incidencia = TriajeIncidencia(
        texto_original="El residente de la 204 dice sentirse mareado",
        categoria="caida",
        urgencia="alta",
        resumen="Mareo con riesgo de caida activo",
        razonamiento="El residente presenta un sintoma corporal con flag de riesgo activo.",
    )
    assert incidencia.categoria == "caida"
    assert incidencia.departamento == "enfermeria"


def test_resumen_demasiado_largo_es_rechazado():
    """Alucinacion real que vimos con Ollama: el modelo ignora el limite de 10 palabras."""
    with pytest.raises(ValidationError):
        TriajeIncidencia(
            texto_original="mareo",
            categoria="caida",
            urgencia="alta",
            resumen="Este es un resumen deliberadamente muy largo que supera las diez palabras permitidas",
            razonamiento="detalle",
        )


def test_categoria_fuera_del_catalogo_es_rechazada():
    """Alucinacion real: el modelo inventa una categoria que no existe en el esquema cerrado."""
    with pytest.raises(ValidationError):
        TriajeIncidencia(
            texto_original="mareo",
            categoria="urgencia_medica",
            urgencia="alta",
            resumen="resumen corto",
            razonamiento="detalle",
        )


@pytest.mark.parametrize(
    "categoria",
    ["caida", "alteracion_estado", "medicacion", "constantes_vitales"],
)
def test_departamento_siempre_es_enfermeria(categoria):
    """Con el alcance recortado a clinico, el departamento es siempre enfermeria."""
    incidencia = TriajeIncidencia(
        texto_original="texto",
        categoria=categoria,
        urgencia="media",
        resumen="resumen corto",
        razonamiento="detalle",
    )
    assert incidencia.departamento == "enfermeria"