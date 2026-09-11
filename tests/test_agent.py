"""
Tests del orquestador del agente: dispatch de tool calling, proteccion
contra argumentos alucinados, herramientas obligatorias, y el limite
de turnos ante bucles sin fin. Todo simulado (mock).
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


def test_agente_rechaza_respuesta_final_sin_herramienta_obligatoria():
    """Caso real que vimos: el modelo intento clasificar sin consultar el
    contexto del residente. El orquestador debe rechazar ese intento y
    forzar que llame a la herramienta antes de aceptar la respuesta."""
    intento_sin_consultar = _respuesta_final({"categoria": "caida", "urgencia": "baja"})
    llama_herramienta = _respuesta_con_tool_call("consultar_residente", {"residente_id": "res-204"})
    respuesta_correcta = _respuesta_final({"categoria": "caida", "urgencia": "alta"})

    ejecutor = MagicMock(return_value=json.dumps({"flags": ["riesgo_caida"]}))

    with patch(
        "app.agent.orchestrator.requests.post",
        side_effect=[intento_sin_consultar, llama_herramienta, respuesta_correcta],
    ) as mock_post:
        resultado = ejecutar_agente(
            modelo="llama3.2:3b",
            system_prompt="...",
            user_prompt="Incidencia: mareo en res-204.",
            herramientas=[{}],
            ejecutores={"consultar_residente": ejecutor},
            herramientas_obligatorias={"consultar_residente"},
        )

    assert json.loads(resultado)["urgencia"] == "alta"
    assert mock_post.call_count == 3


def test_filtrar_argumentos_ignora_claves_alucinadas():
    def funcion_de_prueba(residente_id: str) -> str:
        return residente_id

    filtrados = _filtrar_argumentos_validos(
        funcion_de_prueba,
        {"residente_id": "res-204", "razonamiento": "esto no deberia estar aqui"},
    )
    assert filtrados == {"residente_id": "res-204"}


def test_ejecutar_herramienta_segura_no_rompe_ante_argumento_faltante():
    def funcion_de_prueba(residente_id: str) -> str:
        return residente_id

    resultado = _ejecutar_herramienta_segura(funcion_de_prueba, {})
    data = json.loads(resultado)
    assert "error" in data