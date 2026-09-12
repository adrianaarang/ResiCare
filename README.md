# ResiCare

Motor de triaje inteligente para el **Libro de Incidencias de Enfermeria** en residencias de ancianos. Clasifica automaticamente el texto libre de una incidencia (categoria, urgencia, resumen) usando un LLM, con el contexto clinico real del residente (flags de riesgo, condiciones cronicas) y el historial de incidencias pasadas — pero siempre con un profesional validando la decision final antes de registrarla (human-in-the-loop).

## Que hace

- **Clasifica incidencias clinicas** (caida, alteracion de estado, medicacion, constantes vitales) con nivel de urgencia (critica/alta/media/baja)
- **Razona con contexto real**: un agente con arquitectura ReAct decide por si mismo cuando consultar el historial clinico del residente antes de clasificar, en vez de recibirlo todo ya masticado
- **Detecta reincidencia** via RAG (busqueda semantica en el historico de incidencias, con ChromaDB), de forma determinista: el sistema garantiza el aviso aunque el razonamiento del LLM no lo explique bien
- **Compara dos proveedores de LLM**: un modelo local via Ollama (gratis, sin limites de uso) frente a uno comercial via Groq (de pago por uso), midiendo coste, latencia y calidad de clasificacion
- **Persiste todo** en un Libro de Incidencias (SQLite), organizado por residente -> ano -> mes -> dia -> turno de enfermeria
- **Autenticacion de personal**: usuario y contrasena (cifrada con PBKDF2), cambio de contrasena obligatorio en el primer acceso, y recuperacion via pregunta secreta. Un rol de administrador puede dar de alta y baja al resto del personal
- Validacion estricta con Pydantic: si el LLM alucina un formato incorrecto, el sistema lo detecta y le pide que se corrija, sin romper el servicio

## Arquitectura

app/
├── main.py # API FastAPI: triaje, libro, metricas, personal, login
├── schemas/ # Modelos Pydantic (Residente, TriajeIncidencia)
├── agent/ # Prompts, herramientas y orquestador del agente ReAct
├── rag/ # Embeddings (Ollama) + ChromaDB para deteccion de reincidencia
├── providers/ # Interfaz comun LLMProvider + implementaciones (Ollama, Groq)
└── core/
├── retry.py # Reintento con auto-correccion ante fallos de validacion
├── http_retry.py # Backoff exponencial ante rate limits (429) del proveedor externo
├── metrics.py # Agregacion de coste/tokens/latencia por proveedor
├── almacen.py # Persistencia SQLite del Libro de Incidencias
└── personal.py # Autenticacion: login, hash de contrasenas, recuperacion

data/ # Datos de ejemplo, base de datos SQLite, indice ChromaDB
tests/ # Bateria de tests con Pytest
resicare-dashboard/ # Frontend en React (Vite)


## Requisitos

- Python 3.10+
- Node.js (para el frontend en React)
- [Ollama](https://ollama.com) instalado, con estos modelos descargados:

ollama pull llama3.2:3b
ollama pull nomic-embed-text

- Una API key gratuita de [Groq](https://console.groq.com/keys) (para el proveedor comercial)

## Instalacion

```bash
pip install -r requirements.txt
```

Crea un archivo `.env` en la raiz con tu clave de Groq:

GROQ_API_KEY=tu_clave_aqui


**Personal inicial:** el repositorio no incluye `data/personal.json` con credenciales reales (esta en `.gitignore`). Consulta `data/personal.example.json` para ver la estructura, o genera tu propio administrador inicial ejecutando esto una vez:

```python
from app.core.personal import _hash, _nueva_sal
import json

sal = _nueva_sal()
admin = {
    "id": "enf-admin01", "nombre": "Tu Nombre", "usuario": "tuusuario",
    "rol": "administrador", "password_hash": _hash("tu_contrasena_inicial", sal),
    "sal": sal, "debe_cambiar_password": True,
    "pregunta_secreta": None, "respuesta_hash": None, "respuesta_sal": None,
}
json.dump([admin], open("data/personal.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
```

Al entrar por primera vez, el sistema pedira cambiar esa contrasena y fijar una pregunta secreta para poder recuperarla en el futuro.

## Ejecucion

**1. Arranca Ollama** (normalmente corre en segundo plano tras instalarlo; si no, `ollama serve`)

**2. Arranca el backend:**
```bash
uvicorn app.main:app --reload
```
La API queda disponible en `http://127.0.0.1:8000`, con documentacion interactiva en `http://127.0.0.1:8000/docs`.

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

16 tests cubriendo: validacion del esquema (incluyendo alucinaciones estructurales del LLM), el orquestador del agente (tool calling, argumentos alucinados, herramientas obligatorias), y el endpoint completo (input valido, alucinacion persistente, validacion de entrada).

## Endpoints principales

| Endpoint | Metodo | Descripcion |
|---|---|---|
| `/triaje` | POST | Clasifica una incidencia. `modo`: `unico` (un proveedor) o `comparar` (ambos) |
| `/libro` | GET | Historial de incidencias, opcionalmente filtrado por `residente_id` |
| `/residentes` | GET | Lista de residentes (id + habitacion) |
| `/personal` | GET/POST | Listado / alta de personal |
| `/personal/{id}` | DELETE | Baja de personal |
| `/login` | POST | Autenticacion (usuario + contrasena) |
| `/cambiar-password` | POST | Cambio de contrasena (obligatorio en el primer acceso) |
| `/recuperar-password/pregunta` | GET | Obtiene la pregunta secreta de un usuario |
| `/recuperar-password/restablecer` | POST | Restablece la contrasena si la respuesta secreta es correcta |
| `/metricas` | GET | Totales acumulados de coste/tokens/latencia por proveedor |
| `/salud` | GET | Comprobacion basica de que el servicio esta activo |

## Decisiones de diseno relevantes

- **Alcance recortado a incidencias clinicas**: el proyecto se centra en el libro de novedades de enfermeria, no en incidencias de infraestructura, farmacia o personal en general.
- **El agente fuerza el uso de herramientas de forma limitada**: se probo exigir el uso obligatorio de ambas herramientas (consultar residente + buscar reincidencia) antes de aceptar la respuesta del modelo local, pero esto generaba bucles inestables con el modelo pequeno (llama3.2:3b). Se priorizo la estabilidad del servicio sobre la garantia estricta, documentando esta limitacion del modelo local frente al comercial.
- **`temperature=0` en Ollama**: se detecto que el mismo texto de entrada podia producir clasificaciones distintas en llamadas separadas (muestreo aleatorio por defecto). Se fijo `temperature=0` para clasificaciones deterministas y reproducibles.
- **La comparacion entre proveedores usa clasificacion directa** (sin agente/tool calling) para ambos, con el contexto del residente ya resuelto e inyectado en el prompt — asi se compara la calidad del modelo en si, sin que la capacidad de tool calling de cada uno distorsione el resultado.
- **La deteccion de reincidencia es determinista, no depende del LLM**: el backend consulta el RAG por su cuenta tras cada clasificacion y adjunta el resultado (casos similares, con fecha y similitud) de forma garantizada, en vez de confiar en que el modelo lo mencione bien en su razonamiento.
- **Autenticacion simple, no de nivel produccion**: pensada para uso en la intranet de la residencia (sin tokens de sesion, sin limite de intentos de login). Las contrasenas y respuestas secretas se guardan siempre cifradas (PBKDF2 + sal por usuario), nunca en texto plano.