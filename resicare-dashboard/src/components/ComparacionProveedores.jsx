import { useState, useEffect } from "react";
import { enviarTriaje, obtenerResidentes } from "../api";

const COLOR_URGENCIA = {
  critica: "#B3261E",
  alta: "#C77C1E",
  media: "#8A8D1F",
  baja: "#5F5E5A",
};

const NOMBRE_PROVEEDOR = {
  ollama: "Ollama (local)",
  groq: "Groq (comercial)",
};

function fechaDeHoy() {
  return new Date().toISOString().split("T")[0];
}

function ColumnaResultado({ nombre, datos }) {
  if (datos.error) {
    return (
      <div className="tarjeta-incidencia columna-comparacion">
        <h4>{NOMBRE_PROVEEDOR[nombre]}</h4>
        <p className="error">Error: {datos.error}</p>
      </div>
    );
  }

  const { resultado, metricas, intentos, reincidencia } = datos;

  return (
    <div className="tarjeta-incidencia columna-comparacion">
      <h4>{NOMBRE_PROVEEDOR[nombre]}</h4>

      <div className="tarjeta-cabecera">
        <span className="etiqueta-urgencia" style={{ backgroundColor: COLOR_URGENCIA[resultado.urgencia] }}>
          {resultado.urgencia}
        </span>
        <span className="tarjeta-fecha">{intentos} intento(s)</span>
      </div>

      <p className="tarjeta-texto">{resultado.resumen}</p>
      <p className="tarjeta-detalle"><strong>{resultado.categoria}</strong></p>
      <p className="tarjeta-razonamiento">{resultado.razonamiento}</p>

      {metricas && (
        <div className="metricas-comparacion">
          <div><span>Latencia</span><strong>{metricas.latencia_ms} ms</strong></div>
          <div><span>Tokens</span><strong>{metricas.tokens_entrada} → {metricas.tokens_salida}</strong></div>
          <div><span>Coste</span><strong>${metricas.coste_usd}</strong></div>
        </div>
      )}

      {reincidencia?.detectada && (
        <div className="aviso-reincidencia">
          ⚠ {reincidencia.casos.length} incidencia(s) similar(es) detectada(s)
        </div>
      )}
    </div>
  );
}

function ComparacionProveedores() {
  const [texto, setTexto] = useState("");
  const [residentes, setResidentes] = useState([]);
  const [residenteId, setResidenteId] = useState("");
  const [fechaIncidente, setFechaIncidente] = useState(fechaDeHoy());
  const [turno, setTurno] = useState("");

  const [resultados, setResultados] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    obtenerResidentes().then(setResidentes).catch(() => {});
  }, []);

  async function manejarEnvio(e) {
    e.preventDefault();

    setCargando(true);
    setError(null);
    setResultados(null);

    try {
      const respuesta = await enviarTriaje({
        texto,
        residenteId,
        modo: "comparar",
        proveedor: "ollama",
        turno,
        fechaIncidente,
      });
      setResultados(respuesta);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div>
      <h2>Comparar proveedores</h2>
      <p className="descripcion-comparar">
        Envía la misma incidencia a Ollama (local) y Groq (comercial) a la vez,
        para comparar coste, latencia y calidad de clasificación.
      </p>

      <form onSubmit={manejarEnvio} className="formulario-triaje">
        <label>
          Texto de la incidencia
          <textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Ej: dice sentirse mareado al levantarse de la silla"
            rows={3}
            required
          />
        </label>

        <label>
          Habitación
          <select value={residenteId} onChange={(e) => setResidenteId(e.target.value)} required>
            <option value="" disabled>Selecciona una habitación</option>
            {residentes.map((r) => (
              <option key={r.id} value={r.id}>Habitación {r.habitacion}</option>
            ))}
          </select>
        </label>

        <div className="fila-formulario">
          <label>
            Día
            <input type="date" value={fechaIncidente} onChange={(e) => setFechaIncidente(e.target.value)} required />
          </label>

          <label>
            Turno
            <select value={turno} onChange={(e) => setTurno(e.target.value)} required>
              <option value="" disabled>Selecciona un turno</option>
              <option value="manana">Mañana</option>
              <option value="tarde">Tarde</option>
              <option value="noche">Noche</option>
            </select>
          </label>
        </div>

        <button type="submit" disabled={cargando}>
          {cargando ? "Comparando..." : "Comparar proveedores"}
        </button>
      </form>

      {error && <p className="error">Error: {error}</p>}

      {resultados && (
        <div className="grid-comparacion">
          <ColumnaResultado nombre="ollama" datos={resultados.ollama} />
          <ColumnaResultado nombre="groq" datos={resultados.groq} />
        </div>
      )}
    </div>
  );
}

export default ComparacionProveedores;