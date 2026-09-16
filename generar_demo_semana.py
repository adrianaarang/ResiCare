import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# 5 incidencias para el residente 204, repartidas en la ultima semana,
# en distintos turnos. Las 3 de "mareo/inestable" deberian dispararse
# reincidencia entre si via RAG.
incidencias = [
    {
        "texto": "El residente de la 204 dice sentirse mareado al levantarse de la silla",
        "fecha_incidente": "2026-09-10",
        "turno": "manana",
    },
    {
        "texto": "Ha vuelto a sentirse inestable al ponerse de pie",
        "fecha_incidente": "2026-09-12",
        "turno": "tarde",
    },
    {
        "texto": "Se queja de dolor en la rodilla derecha al caminar",
        "fecha_incidente": "2026-09-13",
        "turno": "noche",
    },
    {
        "texto": "Se ha mareado de nuevo al levantarse de la cama esta manana",
        "fecha_incidente": "2026-09-15",
        "turno": "manana",
    },
    {
        "texto": "Tiene fiebre de 38 grados y algo de tos",
        "fecha_incidente": "2026-09-16",
        "turno": "tarde",
    },
]

for i, inc in enumerate(incidencias, 1):
    payload = {
        "texto": inc["texto"],
        "residente_id": "res-204",
        "modo": "unico",
        "proveedor": "ollama",
        "turno": inc["turno"],
        "fecha_incidente": inc["fecha_incidente"],
    }
    print(f"[{i}/{len(incidencias)}] Enviando: {inc['texto'][:50]}...")
    r = requests.post(f"{BASE_URL}/triaje", json=payload, timeout=120)
    if r.status_code == 200:
        data = r.json()
        urgencia = data["resultado"]["urgencia"]
        reincidencia = data.get("reincidencia", {}).get("detectada", False)
        print(f"    -> urgencia: {urgencia} | reincidencia detectada: {reincidencia}")
    else:
        print(f"    -> ERROR {r.status_code}: {r.text[:200]}")
    time.sleep(1)

print("\nListo. Revisa la pestana 'Libro de Incidencias' para el residente 204.")