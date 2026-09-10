"""
Tests del orquestador del agente: dispatch de tool calling, proteccion
contra argumentos alucinados, y el limite de turnos ante bucles sin fin.
Todo simulado (mock) para no depender de tener Ollama corriendo.
"""
import json
from unittest.mock import patch, MagicMock

import pytest

from app.agent.orchestrator import (
    ejecutar_agente,
    _filtrar_argumentos_validos,
    _ejecutar_herramienta_segura,
)


def _respuesta_con_tool_call(nombre_funcion: str, argumentos: dict):
    r = MagicMock()
    r.raise_for_status.return_value = None
    r.json.return_value = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": nombre_funcion, "arguments": argumentos}}],
        }
    }
    return r


def _respuesta_final(contenido: dict):
    r = MagicMock()
    r.raise_for_status.return_value = None
    r.json.return_value = {
        "message": {"role": "assistant", "content": json.dumps(contenido), "tool_calls": None}
    }
    return r


def test_agente_llama_a_la_herramienta_y_devuelve_respuesta_final():
    """Ciclo ReAct basico: pide una herramienta, la recibe, responde."""
    turno_1 = _respuesta_con_tool_call("consultar_residente", {"residente_id": "res-204"})
    turno_2 = _respuesta_final({"categoria": "clinica", "urgencia": "alta"})

    llamadas_registradas = []

    def ejecutor(residente_id: str) -> str:
        llamadas_registradas.append(residente_id)
        return json.dumps({"flags": ["riesgo_caida"]})

    with patch("app.agent.orchestrator.requests.post", side_effect=[turno_1, turno_2]):
        resultado = ejecutar_agente(
            modelo="llama3.2:3b",
            system_prompt="...",
            user_prompt="Incidencia: mareo en res-204.",
            herramientas=[{}],
            ejecutores={"consultar_residente": ejecutor},
        )

    assert json.loads(resultado)["categoria"] == "clinica"
    assert llamadas_registradas == ["res-204"]


def test_agente_agota_turnos_lanza_runtime_error():
    """Si el modelo nunca deja de pedir herramientas, no debe colgarse:
    debe fallar de forma controlada tras max_turnos."""
    turno_que_nunca_termina = _respuesta_con_tool_call("consultar_residente", {"residente_id": "res-204"})
    ejecutor = MagicMock(return_value="{}")

    with patch("app.agent.orchestrator.requests.post", return_value=turno_que_nunca_termina):
        with pytest.raises(RuntimeError):
            ejecutar_agente(
                modelo="llama3.2:3b",
                system_prompt="...",
                user_prompt="Incidencia: mareo.",
                herramientas=[{}],
                ejecutores={"consultar_residente": ejecutor},
                max_turnos=3,
            )


def test_filtrar_argumentos_ignora_claves_alucinadas():
    """Caso real que ocurrio con Ollama: el modelo anadio 'razonamiento'
    a una llamada que solo acepta 'residente_id'."""
    def funcion_de_prueba(residente_id: str) -> str:
        return residente_id

    filtrados = _filtrar_argumentos_validos(
        funcion_de_prueba,
        {"residente_id": "res-204", "razonamiento": "esto no deberia estar aqui"},
    )
    assert filtrados == {"residente_id": "res-204"}


def test_ejecutar_herramienta_segura_no_rompe_ante_argumento_faltante():
    """Si al modelo se le olvida un argumento obligatorio, se captura como
    error controlado en vez de propagar la excepcion."""
    def funcion_de_prueba(residente_id: str) -> str:
        return residente_id

    resultado = _ejecutar_herramienta_segura(funcion_de_prueba, {})
    data = json.loads(resultado)
    assert "error" in data