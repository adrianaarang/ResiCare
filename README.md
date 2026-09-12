<p align="center">
  <img src="docs/resicare_logo.png" alt="ResiCare" width="450">
</p>

# ResiCare

Motor de triaje inteligente para el **Libro de Incidencias de Enfermería** en residencias de ancianos. Clasifica automáticamente el texto libre de una incidencia (categoría, urgencia, resumen) usando un LLM, con el contexto clínico real del residente (flags de riesgo, condiciones crónicas) y el historial de incidencias pasadas — pero siempre con un profesional validando la decisión final antes de registrarla (human-in-the-loop).

## Qué hace

- **Clasifica incidencias clínicas** (caída, alteración de estado, medicación, constantes vitales) con nivel de urgencia (crítica/alta/media/baja)
- **Razona con contexto real**: un agente con arquitectura ReAct decide por sí mismo cuándo consultar el historial clínico del residente antes de clasificar, en vez de recibirlo todo ya masticado
- **Detecta reincidencia** vía RAG (búsqueda semántica en el histórico de incidencias, con ChromaDB), de forma determinista: el sistema garantiza el aviso aunque el razonamiento del LLM no lo explique bien
- **Compara dos proveedores de LLM**: un modelo local vía Ollama (gratis, sin límites de uso) frente a uno comercial vía Groq (de pago por uso), midiendo coste, latencia y calidad de clasificación
- **Persiste todo** en un Libro de Incidencias (SQLite), organizado por residente → año → mes → día → turno de enfermería
- **Autenticación de personal**: usuario y contraseña (cifrada con PBKDF2), cambio de contraseña obligatorio en el primer acceso, y recuperación vía pregunta secreta. Un rol de administrador puede dar de alta y baja al resto del personal
- Validación estricta con Pydantic: si el LLM alucina un formato incorrecto, el sistema lo detecta y le pide que se corrija, sin romper el servicio

## Arquitectura

```
app/
├── main.py              # API FastAPI: triaje, libro, metricas, personal, login
├── schemas/              # Modelos Pydantic (Residente, TriajeIncidencia)
├── agent/                # Prompts, herramientas y orquestador del agente ReAct
├── rag/                  # Embeddings (Ollama) + ChromaDB para detección de reincidencia
├── providers/            # Interfaz común LLMProvider + implementaciones (Ollama, Groq)
└── core/
    ├── retry.py          # Reintento con auto-corrección ante fallos de validación
    ├── http_retry.py     # Backoff exponencial ante rate limits (429) del proveedor externo
    ├── metrics.py         # Agregación de coste/tokens/latencia por proveedor
    ├── almacen.py         # Persistencia SQLite del Libro de Incidencias
    └── personal.py        # Autenticación: login, hash de contraseñas, recuperación

data/                     # Datos de ejemplo, base de datos SQLite, índice ChromaDB
tests/                    # Batería de tests con Pytest
resicare-dashboard/       # Frontend en React (Vite)
```

## Requisitos

- Python 3.10+
- Node.js (para el frontend en React)
- [Ollama](https://ollama.com) instalado, con estos modelos descargados:
  ```
  ollama pull llama3.2:3b
  ollama pull nomic-embed-text
  ```
- Una API key gratuita de [Groq](https://console.groq.com/keys) (para el proveedor comercial)

## Instalación

```bash
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz con tu clave de Groq:
```
GROQ_API_KEY=tu_clave_aqui
```

**Personal inicial:** el repositorio no incluye `data/personal.json` con credenciales reales (está en `.gitignore`). Consulta `data/personal.example.json` para ver la estructura, o genera tu propio administrador inicial ejecutando esto una vez:

```python
from app.core.personal import _hash, _nueva_sal
import json

sal = _nueva_sal()
admin = {
    "id": "enf-admin01", "nombre": "Tu Nombre", "usuario": "tuusuario",
    "rol": "administrador", "password_hash": _hash("tu_contraseña_inicial", sal),
    "sal": sal, "debe_cambiar_password": True,
    "pregunta_secreta": None, "respuesta_hash": None, "respuesta_sal": None,
}
json.dump([admin], open("data/personal.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
```

Al entrar por primera vez, el sistema pedirá cambiar esa contraseña y fijar una pregunta secreta para poder recuperarla en el futuro.

## Ejecución

**1. Arranca Ollama** (normalmente corre en segundo plano tras instalarlo; si no, `ollama serve`)

**2. Arranca el backend:**
```bash
uvicorn app.main:app --reload
```
La API queda disponible en `http://127.0.0.1:8000`, con documentación interactiva en `http://127.0.0.1:8000/docs`.

**3. Arranca el frontend** (en otra terminal):
```bash
cd resicare-dashboard
npm install
npm run dev
```
El dashboard queda disponible en `http://localhost:5173`.

## Tests

```bash
pytest tests/ -v
```

16 tests cubriendo: validación del esquema (incluyendo alucinaciones estructurales del LLM), el orquestador del agente (tool calling, argumentos alucinados, herramientas obligatorias), y el endpoint completo (input válido, alucinación persistente, validación de entrada).

## Endpoints principales

| Endpoint | Método | Descripción |
|---|---|---|
| `/triaje` | POST | Clasifica una incidencia. `modo`: `unico` (un proveedor) o `comparar` (ambos) |
| `/libro` | GET | Historial de incidencias, opcionalmente filtrado por `residente_id` |
| `/residentes` | GET | Lista de residentes (id + habitación) |
| `/personal` | GET/POST | Listado / alta de personal |
| `/personal/{id}` | DELETE | Baja de personal |
| `/login` | POST | Autenticación (usuario + contraseña) |
| `/cambiar-password` | POST | Cambio de contraseña (obligatorio en el primer acceso) |
| `/recuperar-password/pregunta` | GET | Obtiene la pregunta secreta de un usuario |
| `/recuperar-password/restablecer` | POST | Restablece la contraseña si la respuesta secreta es correcta |
| `/metricas` | GET | Totales acumulados de coste/tokens/latencia por proveedor |
| `/salud` | GET | Comprobación básica de que el servicio está activo |

## Decisiones de diseño relevantes

- **Alcance recortado a incidencias clínicas**: el proyecto se centra en el libro de novedades de enfermería, no en incidencias de infraestructura, farmacia o personal en general.
- **El agente fuerza el uso de herramientas de forma limitada**: se probó exigir el uso obligatorio de ambas herramientas (consultar residente + buscar reincidencia) antes de aceptar la respuesta del modelo local, pero esto generaba bucles inestables con el modelo pequeño (llama3.2:3b). Se priorizó la estabilidad del servicio sobre la garantía estricta, documentando esta limitación del modelo local frente al comercial.
- **`temperature=0` en Ollama**: se detectó que el mismo texto de entrada podía producir clasificaciones distintas en llamadas separadas (muestreo aleatorio por defecto). Se fijó `temperature=0` para clasificaciones deterministas y reproducibles.
- **La comparación entre proveedores usa clasificación directa** (sin agente/tool calling) para ambos, con el contexto del residente ya resuelto e inyectado en el prompt — así se compara la calidad del modelo en sí, sin que la capacidad de tool calling de cada uno distorsione el resultado.
- **La detección de reincidencia es determinista, no depende del LLM**: el backend consulta el RAG por su cuenta tras cada clasificación y adjunta el resultado (casos similares, con fecha y similitud) de forma garantizada, en vez de confiar en que el modelo lo mencione bien en su razonamiento.
- **Autenticación simple, no de nivel producción**: pensada para uso en la intranet de la residencia (sin tokens de sesión, sin límite de intentos de login). Las contraseñas y respuestas secretas se guardan siempre cifradas (PBKDF2 + sal por usuario), nunca en texto plano.
