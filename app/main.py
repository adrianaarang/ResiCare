"""
API principal de ResiCare: expone el motor de triaje via FastAPI.
"""
import json
from typing import Optional, Literal

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.schemas.triaje import TriajeIncidencia
from app.schemas.residente import Residente
from app.agent.prompts import SYSTEM_PROMPT, construir_user_prompt
from app.agent.tools import consultar_residente, TOOL_CONSULTAR_RESIDENTE, HERRAMIENTAS_DISPONIBLES
from app.agent.orchestrator import ejecutar_agente
from app.providers.ollama_provider import OllamaProvider
from app.providers.comercial_provider import GroqProvider
from app.core.retry import validar_con_reintento, TriajeFallidoError
from app.core.metrics import registro_global
from app.core.almacen import inicializar_db, guardar_incidencia, listar_incidencias
from app.rag.vectorstore import (
    TOOL_BUSCAR_INCIDENCIAS_SIMILARES,
    buscar_incidencias_similares,
    indexar_historico,
    indexar_nueva_incidencia,
)

app = FastAPI(title="ResiCare - Motor de triaje")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

indexar_historico()
inicializar_db()

HERRAMIENTAS_AGENTE = [TOOL_CONSULTAR_RESIDENTE, TOOL_BUSCAR_INCIDENCIAS_SIMILARES]
EJECUTORES_AGENTE = {
    **HERRAMIENTAS_DISPONIBLES,
    "buscar_incidencias_similares": buscar_incidencias_similares,
}

SYSTEM_PROMPT_AGENTE = SYSTEM_PROMPT + (
    "\n\nHERRAMIENTAS DISPONIBLES (uso obligatorio, no opcional):\n"
    "- Si el texto menciona un identificador de residente (ej. 'res-204'), DEBES llamar "
    "SIEMPRE a consultar_residente antes de responder, sin excepcion.\n"
    "- DEBES llamar tambien a buscar_incidencias_similares antes de responder.\n"
    "No respondas con la clasificacion final hasta haber llamado a AMBAS herramientas "
    "cuando el texto incluya un id de residente."
)


class TriajeRequest(BaseModel):
    texto: str
    residente_id: Optional[str] = None
    modo: Literal["unico", "comparar"] = "unico"
    proveedor: Literal["ollama", "groq"] = "ollama"


def _obtener_residente(residente_id: Optional[str]) -> Optional[Residente]:
    if not residente_id:
        return None
    resultado = json.loads(consultar_residente(residente_id))
    if "error" in resultado:
        return None
    return Residente(**resultado)


def _guardar_en_libro_y_rag(incidencia: TriajeIncidencia, proveedor: str) -> None:
    incidencia_id, fecha_iso = guardar_incidencia(incidencia, proveedor=proveedor)
    indexar_nueva_incidencia(
        incidencia_id=f"libro-{incidencia_id}",
        texto=incidencia.texto_original,
        residente_id=incidencia.residente_id,
        categoria=incidencia.categoria,
        urgencia=incidencia.urgencia,
        fecha_iso=fecha_iso,
    )


def _clasificar_directo(provider, texto: str, residente_id: Optional[str]):
    residente = _obtener_residente(residente_id)
    user_prompt = construir_user_prompt(texto, residente)

    metricas_capturadas = {}

    def llamar(system_prompt: str, user_prompt: str) -> str:
        respuesta = provider.generar(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=TriajeIncidencia.model_json_schema(),
        )
        metricas_capturadas["ultima"] = respuesta
        return respuesta.contenido

    incidencia, intentos = validar_con_reintento(
        funcion_generadora=llamar,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        esquema=TriajeIncidencia,
        max_intentos=3,
    )

    metrica = metricas_capturadas["ultima"]
    registro_global.registrar(
        proveedor=metrica.proveedor,
        tokens_entrada=metrica.tokens_entrada,
        tokens_salida=metrica.tokens_salida,
        latencia_ms=metrica.latencia_ms,
        coste_usd=metrica.coste_usd,
    )

    return incidencia, intentos, metrica


def _clasificar_con_agente(texto: str, residente_id: Optional[str]):
    user_prompt_base = f"Incidencia: {texto}"
    if residente_id:
        user_prompt_base += f" (id: {residente_id})"

    def llamar(system_prompt: str, user_prompt: str) -> str:
        return ejecutar_agente(
            modelo="llama3.2:3b",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            herramientas=HERRAMIENTAS_AGENTE,
            ejecutores=EJECUTORES_AGENTE,
            json_schema=TriajeIncidencia.model_json_schema(),
            herramientas_obligatorias={"consultar_residente", "buscar_incidencias_similares"} if residente_id else None,
        )

    incidencia, intentos = validar_con_reintento(
        funcion_generadora=llamar,
        system_prompt=SYSTEM_PROMPT_AGENTE,
        user_prompt=user_prompt_base,
        esquema=TriajeIncidencia,
        max_intentos=3,
    )
    return incidencia, intentos


@app.get("/salud")
def salud():
    return {"estado": "ok"}


@app.get("/metricas")
def metricas():
    return registro_global.resumen()


@app.get("/libro")
def libro(residente_id: Optional[str] = None, limite: int = 100):
    return listar_incidencias(residente_id=residente_id, limite=limite)


@app.post("/triaje")
def triaje(payload: TriajeRequest):
    try:
        if payload.modo == "unico":
            if payload.proveedor == "ollama":
                incidencia, intentos = _clasificar_con_agente(payload.texto, payload.residente_id)
                _guardar_en_libro_y_rag(incidencia, proveedor="ollama")
                return {
                    "proveedor": "ollama",
                    "modo": "agente_react",
                    "intentos": intentos,
                    "resultado": incidencia.model_dump(),
                }
            else:
                provider = GroqProvider()
                incidencia, intentos, metrica = _clasificar_directo(
                    provider, payload.texto, payload.residente_id
                )
                _guardar_en_libro_y_rag(incidencia, proveedor="groq")
                return {
                    "proveedor": "groq",
                    "modo": "directo",
                    "intentos": intentos,
                    "resultado": incidencia.model_dump(),
                    "metricas": metrica.model_dump(),
                }

        else:
            resultados = {}
            constructores_provider = {"ollama": OllamaProvider, "groq": GroqProvider}
            for nombre, ConstructorProvider in constructores_provider.items():
                try:
                    provider = ConstructorProvider()
                    incidencia, intentos, metrica = _clasificar_directo(
                        provider, payload.texto, payload.residente_id
                    )
                    _guardar_en_libro_y_rag(incidencia, proveedor=nombre)
                    resultados[nombre] = {
                        "intentos": intentos,
                        "resultado": incidencia.model_dump(),
                        "metricas": metrica.model_dump(),
                    }
                except (TriajeFallidoError, ValueError, RuntimeError) as e:
                    resultados[nombre] = {"error": str(e)}
            return resultados

    except TriajeFallidoError as e:
        raise HTTPException(
            status_code=422,
            detail=f"El modelo no devolvio un formato valido tras varios intentos: {e.ultimo_error}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=422,
            detail=f"El motor de triaje no pudo completar la clasificacion: {str(e)}",
        )