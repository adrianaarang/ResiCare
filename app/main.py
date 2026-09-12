"""
API principal de ResiCare: expone el motor de triaje via FastAPI.

Dos modos de uso:
- modo="unico": clasifica con un solo proveedor. Con Ollama, usa el agente
  completo (ReAct + tool calling). Con Groq, clasifica directamente con el
  contexto del residente ya resuelto.
- modo="comparar": clasifica con AMBOS proveedores sobre el mismo texto.
"""
import json
import uuid
from pathlib import Path
from typing import Optional, Literal

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.schemas.triaje import TriajeIncidencia
from app.schemas.residente import Residente
from app.agent.prompts import SYSTEM_PROMPT, construir_user_prompt
from app.agent.tools import (
    consultar_residente,
    TOOL_CONSULTAR_RESIDENTE,
    HERRAMIENTAS_DISPONIBLES,
    _cargar_residentes,
)
from app.agent.orchestrator import ejecutar_agente
from app.providers.ollama_provider import OllamaProvider
from app.providers.comercial_provider import GroqProvider
from app.core.retry import validar_con_reintento, TriajeFallidoError
from app.core.metrics import registro_global
from app.core.almacen import inicializar_db, guardar_incidencia, listar_incidencias
from app.core.personal import (
    listar_personal_publico,
    crear_personal,
    eliminar_personal,
    verificar_login,
    cambiar_password,
    obtener_pregunta_secreta,
    restablecer_password_con_respuesta,
)
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
    turno: Optional[Literal["manana", "tarde", "noche"]] = None
    fecha_incidente: Optional[str] = None
    registrado_por: Optional[str] = None


def _obtener_residente(residente_id: Optional[str]) -> Optional[Residente]:
    if not residente_id:
        return None
    resultado = json.loads(consultar_residente(residente_id))
    if "error" in resultado:
        return None
    return Residente(**resultado)


def _guardar_en_libro_y_rag(
    incidencia: TriajeIncidencia,
    proveedor: str,
    turno: Optional[str] = None,
    fecha_incidente: Optional[str] = None,
    reincidencia: Optional[dict] = None,
    registrado_por: Optional[str] = None,
) -> None:
    es_reincidencia = bool(reincidencia and reincidencia.get("detectada"))
    fecha_previa = None
    casos_json = None
    if es_reincidencia and reincidencia.get("casos"):
        fecha_previa = reincidencia["casos"][0].get("fecha")
        casos_json = json.dumps(reincidencia["casos"])

    incidencia_id, fecha_iso = guardar_incidencia(
        incidencia,
        proveedor=proveedor,
        turno=turno or "sin_especificar",
        fecha_incidente=fecha_incidente,
        es_reincidencia=es_reincidencia,
        fecha_reincidencia_previa=fecha_previa,
        casos_reincidencia_json=casos_json,
        registrado_por=registrado_por,
    )
    indexar_nueva_incidencia(
        incidencia_id=f"libro-{uuid.uuid4().hex}",
        texto=incidencia.texto_original,
        residente_id=incidencia.residente_id,
        categoria=incidencia.categoria,
        urgencia=incidencia.urgencia,
        fecha_iso=fecha_iso,
    )


def _asegurar_residente_id(incidencia: TriajeIncidencia, residente_id_conocido: Optional[str]) -> TriajeIncidencia:
    if residente_id_conocido and incidencia.residente_id != residente_id_conocido:
        return incidencia.model_copy(update={"residente_id": residente_id_conocido})
    return incidencia


def _detectar_reincidencia(texto: str, residente_id: Optional[str], umbral_similitud: float = 0.6) -> dict:
    if not residente_id:
        return {"detectada": False, "casos": []}

    resultado = json.loads(buscar_incidencias_similares(texto, residente_id=residente_id))
    casos_relevantes = [
        r for r in resultado.get("resultados", [])
        if r.get("similitud", 0) >= umbral_similitud
    ]
    return {
        "detectada": len(casos_relevantes) > 0,
        "casos": casos_relevantes,
    }


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

    metricas_capturadas = {}

    def llamar(system_prompt: str, user_prompt: str) -> str:
        return ejecutar_agente(
            modelo="llama3.2:3b",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            herramientas=HERRAMIENTAS_AGENTE,
            ejecutores=EJECUTORES_AGENTE,
            json_schema=TriajeIncidencia.model_json_schema(),
            herramientas_obligatorias=None,
            max_turnos=6,
            metricas_out=metricas_capturadas,
        )

    incidencia, intentos = validar_con_reintento(
        funcion_generadora=llamar,
        system_prompt=SYSTEM_PROMPT_AGENTE,
        user_prompt=user_prompt_base,
        esquema=TriajeIncidencia,
        max_intentos=3,
    )

    if metricas_capturadas:
        registro_global.registrar(
            proveedor="ollama",
            tokens_entrada=metricas_capturadas.get("tokens_entrada", 0),
            tokens_salida=metricas_capturadas.get("tokens_salida", 0),
            latencia_ms=metricas_capturadas.get("latencia_ms", 0.0),
            coste_usd=0.0,
        )

    return incidencia, intentos


@app.get("/salud")
def salud():
    return {"estado": "ok"}


@app.get("/residentes")
def residentes():
    datos = _cargar_residentes()
    return [
        {"id": r["id"], "habitacion": r["habitacion"]}
        for r in sorted(datos.values(), key=lambda r: r["habitacion"])
    ]


@app.get("/personal")
def personal():
    return listar_personal_publico()


class PersonalRequest(BaseModel):
    nombre: str
    rol: Literal["enfermera", "administrador"] = "enfermera"


@app.post("/personal")
def alta_personal(payload: PersonalRequest):
    return crear_personal(payload.nombre, payload.rol)


@app.delete("/personal/{persona_id}")
def baja_personal(persona_id: str):
    eliminado = eliminar_personal(persona_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="No existe esa persona")
    return {"eliminado": True}


class LoginRequest(BaseModel):
    usuario: str
    password: str


@app.post("/login")
def login(payload: LoginRequest):
    persona = verificar_login(payload.usuario, payload.password)
    if not persona:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {
        "nombre": persona["nombre"],
        "usuario": persona["usuario"],
        "rol": persona["rol"],
        "debe_cambiar_password": persona["debe_cambiar_password"],
    }


class CambiarPasswordRequest(BaseModel):
    usuario: str
    password_actual: str
    password_nueva: str
    pregunta_secreta: Optional[str] = None
    respuesta_secreta: Optional[str] = None


@app.post("/cambiar-password")
def cambiar_password_endpoint(payload: CambiarPasswordRequest):
    ok = cambiar_password(
        payload.usuario, payload.password_actual, payload.password_nueva,
        pregunta_secreta=payload.pregunta_secreta, respuesta_secreta=payload.respuesta_secreta,
    )
    if not ok:
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
    return {"actualizado": True}


@app.get("/recuperar-password/pregunta")
def pregunta_secreta_endpoint(usuario: str):
    pregunta = obtener_pregunta_secreta(usuario)
    if not pregunta:
        raise HTTPException(status_code=404, detail="No hay pregunta secreta configurada para ese usuario")
    return {"pregunta": pregunta}


class RestablecerPasswordRequest(BaseModel):
    usuario: str
    respuesta: str
    password_nueva: str


@app.post("/recuperar-password/restablecer")
def restablecer_password_endpoint(payload: RestablecerPasswordRequest):
    ok = restablecer_password_con_respuesta(payload.usuario, payload.respuesta, payload.password_nueva)
    if not ok:
        raise HTTPException(status_code=401, detail="Respuesta secreta incorrecta")
    return {"restablecido": True}


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
                incidencia = _asegurar_residente_id(incidencia, payload.residente_id)
                reincidencia = _detectar_reincidencia(payload.texto, incidencia.residente_id)
                _guardar_en_libro_y_rag(
                    incidencia, proveedor="ollama",
                    turno=payload.turno, fecha_incidente=payload.fecha_incidente,
                    reincidencia=reincidencia, registrado_por=payload.registrado_por,
                )
                return {
                    "proveedor": "ollama",
                    "modo": "agente_react",
                    "intentos": intentos,
                    "resultado": incidencia.model_dump(),
                    "reincidencia": reincidencia,
                }
            else:
                provider = GroqProvider()
                incidencia, intentos, metrica = _clasificar_directo(
                    provider, payload.texto, payload.residente_id
                )
                incidencia = _asegurar_residente_id(incidencia, payload.residente_id)
                reincidencia = _detectar_reincidencia(payload.texto, incidencia.residente_id)
                _guardar_en_libro_y_rag(
                    incidencia, proveedor="groq",
                    turno=payload.turno, fecha_incidente=payload.fecha_incidente,
                    reincidencia=reincidencia, registrado_por=payload.registrado_por,
                )
                return {
                    "proveedor": "groq",
                    "modo": "directo",
                    "intentos": intentos,
                    "resultado": incidencia.model_dump(),
                    "metricas": metrica.model_dump(),
                    "reincidencia": reincidencia,
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
                    incidencia = _asegurar_residente_id(incidencia, payload.residente_id)
                    reincidencia = _detectar_reincidencia(payload.texto, incidencia.residente_id)
                    _guardar_en_libro_y_rag(
                        incidencia, proveedor=nombre,
                        turno=payload.turno, fecha_incidente=payload.fecha_incidente,
                        reincidencia=reincidencia, registrado_por=payload.registrado_por,
                    )
                    resultados[nombre] = {
                        "intentos": intentos,
                        "resultado": incidencia.model_dump(),
                        "metricas": metrica.model_dump(),
                        "reincidencia": reincidencia,
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