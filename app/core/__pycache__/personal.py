"""
Gestion de personal con autenticacion simple: usuario + contrasena,
cambio de contrasena obligatorio en el primer acceso, y recuperacion
via pregunta secreta.

Pensado para uso en la intranet de una residencia (no es un sistema de
seguridad de nivel produccion: sin tokens de sesion, sin limite de
intentos, etc.), pero las contrasenas y respuestas secretas SIEMPRE
se guardan cifradas (PBKDF2 + sal por usuario), nunca en texto plano.
"""
import hashlib
import json
import os
import unicodedata
from pathlib import Path
from typing import Optional

RUTA_PERSONAL = Path(__file__).parent.parent.parent / "data" / "personal.json"
PASSWORD_INICIAL = "resicare123"


def _quitar_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _generar_usuario(nombre: str, existentes: set) -> str:
    partes = _quitar_acentos(nombre).lower().split()
    if len(partes) < 2:
        base = partes[0] if partes else "usuario"
    else:
        base = partes[0][0] + partes[1]
    base = "".join(c for c in base if c.isalnum())

    usuario = base
    contador = 1
    while usuario in existentes:
        contador += 1
        usuario = f"{base}{contador}"
    return usuario


def _nueva_sal() -> str:
    return os.urandom(16).hex()


def _hash(texto: str, sal: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", texto.encode(), sal.encode(), 100_000).hex()


def listar_personal() -> list[dict]:
    with open(RUTA_PERSONAL, "r", encoding="utf-8") as f:
        return json.load(f)


def _guardar_personal(lista: list[dict]) -> None:
    with open(RUTA_PERSONAL, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)


def listar_personal_publico() -> list[dict]:
    return [
        {"id": p["id"], "nombre": p["nombre"], "usuario": p["usuario"], "rol": p["rol"]}
        for p in listar_personal()
    ]


def _buscar_por_usuario(usuario: str) -> Optional[dict]:
    for p in listar_personal():
        if p["usuario"] == usuario:
            return p
    return None


def crear_personal(nombre: str, rol: str) -> dict:
    lista = listar_personal()
    existentes = {p["usuario"] for p in lista}
    usuario = _generar_usuario(nombre, existentes)
    sal = _nueva_sal()

    nueva = {
        "id": f"enf-{os.urandom(4).hex()}",
        "nombre": nombre,
        "usuario": usuario,
        "rol": rol,
        "password_hash": _hash(PASSWORD_INICIAL, sal),
        "sal": sal,
        "debe_cambiar_password": True,
        "pregunta_secreta": None,
        "respuesta_hash": None,
        "respuesta_sal": None,
    }
    lista.append(nueva)
    _guardar_personal(lista)

    return {
        "id": nueva["id"], "nombre": nombre, "usuario": usuario,
        "rol": rol, "password_inicial": PASSWORD_INICIAL,
    }


def eliminar_personal(persona_id: str) -> bool:
    lista = listar_personal()
    nueva_lista = [p for p in lista if p["id"] != persona_id]
    if len(nueva_lista) == len(lista):
        return False
    _guardar_personal(nueva_lista)
    return True


def verificar_login(usuario: str, password: str) -> Optional[dict]:
    persona = _buscar_por_usuario(usuario)
    if not persona:
        return None
    if _hash(password, persona["sal"]) != persona["password_hash"]:
        return None
    return persona


def cambiar_password(
    usuario: str,
    password_actual: str,
    password_nueva: str,
    pregunta_secreta: Optional[str] = None,
    respuesta_secreta: Optional[str] = None,
) -> bool:
    persona = verificar_login(usuario, password_actual)
    if not persona:
        return False

    lista = listar_personal()
    for p in lista:
        if p["usuario"] == usuario:
            sal_nueva = _nueva_sal()
            p["password_hash"] = _hash(password_nueva, sal_nueva)
            p["sal"] = sal_nueva
            p["debe_cambiar_password"] = False
            if pregunta_secreta and respuesta_secreta:
                sal_resp = _nueva_sal()
                p["pregunta_secreta"] = pregunta_secreta
                p["respuesta_hash"] = _hash(respuesta_secreta.lower().strip(), sal_resp)
                p["respuesta_sal"] = sal_resp
            break
    _guardar_personal(lista)
    return True


def obtener_pregunta_secreta(usuario: str) -> Optional[str]:
    persona = _buscar_por_usuario(usuario)
    if not persona:
        return None
    return persona.get("pregunta_secreta")


def restablecer_password_con_respuesta(usuario: str, respuesta: str, password_nueva: str) -> bool:
    persona = _buscar_por_usuario(usuario)
    if not persona or not persona.get("respuesta_hash"):
        return False
    if _hash(respuesta.lower().strip(), persona["respuesta_sal"]) != persona["respuesta_hash"]:
        return False

    lista = listar_personal()
    for p in lista:
        if p["usuario"] == usuario:
            sal_nueva = _nueva_sal()
            p["password_hash"] = _hash(password_nueva, sal_nueva)
            p["sal"] = sal_nueva
            p["debe_cambiar_password"] = False
            break
    _guardar_personal(lista)
    return True