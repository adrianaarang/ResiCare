import { useState, useEffect } from "react";
import { obtenerLibro } from "../api";

const COLOR_URGENCIA = {
  critica: "#B3261E",
  alta: "#C77C1E",
  media: "#8A8D1F",
  baja: "#5F5E5A",
};

function LibroIncidencias() {
  const [incidencias, setIncidencias] = useState([]);
  const [filtroResidente, setFiltroResidente] = useState("");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  async function cargarLibro() {
    setCargando(true);
    setError(null);
    try {
      const datos = await obtenerLibro(filtroResidente);
      setIncidencias(datos);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargarLibro();
  }, []);

  return (
    <div>
      <h2>Libro de Incidencias</h2>

      <div className="filtro-libro">
        <input
          type="text"
          placeholder="Filtrar por id de residente (ej. res-204)"
          value={filtroResidente}
          onChange={(e) => setFiltroResidente(e.target.value)}
        />
        <button onClick={cargarLibro}>Actualizar</button>
      </div>

      {cargando && <p>Cargando...</p>}
      {error && <p className="error">Error: {error}</p>}

      {!cargando && !error && incidencias.length === 0 && (
        <p>No hay incidencias registradas todavia.</p>
      )}

      <ul className="lista-incidencias">
        {incidencias.map((inc) => (
          <li key={inc.id} className="tarjeta-incidencia">
            <div className="tarjeta-cabecera">
              <span
                className="etiqueta-urgencia"
                style={{ backgroundColor: COLOR_URGENCIA[inc.urgencia] }}
              >
                {inc.urgencia}
              </span>
              <span className="tarjeta-fecha">
                {new Date(inc.fecha).toLocaleString()}
              </span>
            </div>
            <p className="tarjeta-texto">{inc.texto_original}</p>
            <p className="tarjeta-detalle">
              <strong>{inc.categoria}</strong>
              {inc.residente_id && ` · ${inc.residente_id}`}
              {` · via ${inc.proveedor}`}
            </p>
            <p className="tarjeta-razonamiento">{inc.razonamiento}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default LibroIncidencias;
