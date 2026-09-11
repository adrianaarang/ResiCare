"""
Tests del endpoint /triaje con FastAPI TestClient. Todo mockeado (no se
llama a Ollama ni Groq de verdad), para que los tests sean rapidos y
reproducibles sin depender de servicios externos.
"""
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_salud_responde_ok():
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_triaje_con_input_valido_devuelve_200():
    contenido_valido = json.dumps({
        "texto_original": "El residente de la 204 dice sentirse mareado",
        "categoria": "caida",
        "urgencia": "alta",
        "resumen": "Mareo con riesgo de caida",
        "razonamiento": "El residente presenta un sintoma con flag de riesgo activo.",
    })

    with patch("app.main.ejecutar_agente", return_value=contenido_valido), \
         patch("app.main.indexar_nueva_incidencia"):
        respuesta = cliente.post("/triaje", json={
            "texto": "El residente de la 204 dice sentirse mareado",
            "residente_id": "res-204",
            "modo": "unico",
            "proveedor": "ollama",
        })

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["proveedor"] == "ollama"
    assert cuerpo["resultado"]["categoria"] == "caida"
    assert cuerpo["resultado"]["urgencia"] == "alta"
    assert cuerpo["intentos"] == 1


def test_triaje_ante_alucinacion_persistente_devuelve_422_controlado():
    contenido_invalido = json.dumps({
        "texto_original": "mareo",
        "categoria": "caida",
        "urgencia": "alta",
        "resumen": "Este resumen tiene claramente muchas mas de las diez palabras que el esquema permite",
        "razonamiento": "detalle",
    })

    with patch("app.main.ejecutar_agente", return_value=contenido_invalido):
        respuesta = cliente.post("/triaje", json={
            "texto": "El residente de la 204 dice sentirse mareado",
            "residente_id": "res-204",
            "modo": "unico",
            "proveedor": "ollama",
        })

    assert respuesta.status_code == 422
    assert "no devolvio un formato valido" in respuesta.json()["detail"]


def test_triaje_con_texto_vacio_es_rechazado_por_pydantic():
    respuesta = cliente.post("/triaje", json={
        "residente_id": "res-204",
        "modo": "unico",
    })
    assert respuesta.status_code == 422