import { useState, useEffect } from "react";
import { enviarTriaje, obtenerResidentes } from "../api";

const COLOR_URGENCIA = {
  critica: "#B3261E",
  alta: "#C77C1E",
  media: "#8A8D1F",
  baja: "#5F5E5A",
};

function fechaDeHoy() {
  return new Date().toISOString().split("T")[0];
}

function TriajeIndividual() {
  const [texto, setTexto] = useState("");
  const [residentes, setResidentes] = useState([]);
  const [residenteId, setResidenteId] = useState("");
  const [proveedor, setProveedor] = useState("ollama");
  const [fechaIncidente, setFechaIncidente] = useState(fechaDeHoy());
  const [turno, setTurno] = useState("");

  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    obtenerResidentes()
      .then(setResidentes)
      .catch(() => setError("No se pudo cargar la lista de residentes"));
  }, []);

  async function manejarEnvio(e) {
    e.preventDefault();

    setCargando(true);
    setError(null);
    setResultado(null);

    try {
      const respuesta = await enviarTriaje({
        texto,
        residenteId,
        modo: "unico",
        proveedor,
        turno,
        fechaIncidente,
      });
      setResultado(respuesta);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div>
      <h2>Triaje individual</h2>

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
          <select
            value={residenteId}
            onChange={(e) => setResidenteId(e.target.value)}
            required
          >
            <option value="" disabled>
              Selecciona una habitación
            </option>
            {residentes.map((r) => (
              <option key={r.id} value={r.id}>
                Habitación {r.habitacion}
              </option>
            ))}
          </select>
        </label>

        <div className="fila-formulario">
          <label>
            Día
            <input
              type="date"
              value={fechaIncidente}
              onChange={(e) => setFechaIncidente(e.target.value)}
              required
            />
          </label>

          <label>
            Turno
            <select value={turno} onChange={(e) => setTurno(e.target.value)} required>
              <option value="" disabled>
                Selecciona un turno
              </option>
              <option value="manana">Mañana</option>
              <option value="tarde">Tarde</option>
              <option value="noche">Noche</option>
            </select>
          </label>
        </div>

        <label>
          Proveedor
          <select value={proveedor} onChange={(e) => setProveedor(e.target.value)}>
            <option value="ollama">Ollama (local)</option>
            <option value="groq">Groq (comercial)</option>
          </select>
        </label>

        <button type="submit" disabled={cargando}>
          {cargando ? "Clasificando..." : "Triar incidencia"}
        </button>
      </form>

      {error && <p className="error">Error: {error}</p>}

      {resultado && (
        <div className="tarjeta-incidencia resultado-triaje">
          <div className="tarjeta-cabecera">
            <span
              className="etiqueta-urgencia"
              style={{ backgroundColor: COLOR_URGENCIA[resultado.resultado.urgencia] }}
            >
              {resultado.resultado.urgencia}
            </span>
            <span className="tarjeta-fecha">
              {resultado.proveedor} · {resultado.intentos} intento(s)
            </span>
          </div>
          <p className="tarjeta-texto">{resultado.resultado.resumen}</p>
          <p className="tarjeta-detalle">
            <strong>{resultado.resultado.categoria}</strong>
          </p>
          <p className="tarjeta-razonamiento">{resultado.resultado.razonamiento}</p>

          {resultado.reincidencia && resultado.reincidencia.detectada && (
            <div className="aviso-reincidencia">
              ⚠ Reincidencia detectada: {resultado.reincidencia.casos.length} incidencia(s)
              similar(es) reciente(s) para este residente.
              <ul>
                {resultado.reincidencia.casos.map((c, i) => (
                  <li key={i}>
                    {c.fecha} — {c.texto} (similitud {c.similitud})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default TriajeIndividual;