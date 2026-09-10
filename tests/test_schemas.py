"""
Tests del esquema Pydantic TriajeIncidencia: casos validos y las
alucinaciones estructurales que ya vimos en la practica (resumen
demasiado largo, categoria/subcategoria inconsistentes).
"""
import pytest
from pydantic import ValidationError

from app.schemas.triaje import TriajeIncidencia


def test_incidencia_valida_se_acepta():
    incidencia = TriajeIncidencia(
        texto_original="El residente de la 204 dice sentirse mareado",
        categoria="clinica",
        subcategoria="caida",
        urgencia="alta",
        resumen="Mareo con riesgo de caida activo",
        razonamiento="El residente presenta un sintoma corporal con flag de riesgo activo.",
    )
    assert incidencia.categoria == "clinica"
    assert incidencia.departamento == "enfermeria"


def test_resumen_demasiado_largo_es_rechazado():
    """Alucinacion real que vimos con Ollama: el modelo ignora el limite de 10 palabras."""
    with pytest.raises(ValidationError):
        TriajeIncidencia(
            texto_original="mareo",
            categoria="clinica",
            subcategoria="caida",
            urgencia="alta",
            resumen="Este es un resumen deliberadamente muy largo que supera las diez palabras permitidas",
            razonamiento="detalle",
        )


def test_subcategoria_incoherente_con_categoria_es_rechazada():
    """Alucinacion real: el modelo mezcla una subcategoria de otra categoria (ej. 'averia' en 'clinica')."""
    with pytest.raises(ValidationError):
        TriajeIncidencia(
            texto_original="mareo",
            categoria="clinica",
            subcategoria="averia",
            urgencia="alta",
            resumen="resumen corto",
            razonamiento="detalle",
        )


def test_categoria_fuera_del_catalogo_es_rechazada():
    """Alucinacion real: el modelo inventa una categoria que no existe en el esquema cerrado."""
    with pytest.raises(ValidationError):
        TriajeIncidencia(
            texto_original="mareo",
            categoria="urgencia_medica",
            subcategoria="caida",
            urgencia="alta",
            resumen="resumen corto",
            razonamiento="detalle",
        )


@pytest.mark.parametrize(
    "categoria,departamento_esperado",
    [
        ("clinica", "enfermeria"),
        ("suministros_farmacia", "farmacia"),
        ("infraestructura_mantenimiento", "mantenimiento"),
        ("personal_organizacion", "direccion_rrhh"),
    ],
)
def test_departamento_se_deriva_correctamente(categoria, departamento_esperado):
    """El departamento nunca lo decide el LLM, se calcula: menos superficie de alucinacion."""
    subcategoria_valida = {
        "clinica": "caida",
        "suministros_farmacia": "falta_stock",
        "infraestructura_mantenimiento": "averia",
        "personal_organizacion": "cobertura_turno",
    }[categoria]

    incidencia = TriajeIncidencia(
        texto_original="texto",
        categoria=categoria,
        subcategoria=subcategoria_valida,
        urgencia="media",
        resumen="resumen corto",
        razonamiento="detalle",
    )
    assert incidencia.departamento == departamento_esperado