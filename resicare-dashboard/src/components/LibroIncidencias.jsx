import { useState, useEffect } from "react";
import { obtenerLibro, obtenerResidentes } from "../api";

const COLOR_URGENCIA = {
  critica: "#B3261E",
  alta: "#C77C1E",
  media: "#8A8D1F",
  baja: "#5F5E5A",
};

const TURNOS_ORDENADOS = ["manana", "tarde", "noche"];
const NOMBRE_TURNO = { manana: "Mañana", tarde: "Tarde", noche: "Noche" };

const NOMBRES_MES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

function formatearFechaCorta(fechaISO) {
  if (!fechaISO || !fechaISO.includes("-")) return fechaISO;
  const [anio, mes, dia] = fechaISO.split("-");
  return `${dia}/${mes}/${anio}`;
}

function construirIndice(incidencias) {
  const indice = {};

  for (const inc of incidencias) {
    const residente = inc.residente_id || "Sin residente asignado";
    const fecha = inc.fecha_incidente;
    if (!fecha || !fecha.includes("-")) continue;
    const [anio, mes, dia] = fecha.split("-");
    const turno = TURNOS_ORDENADOS.includes(inc.turno) ? inc.turno : "manana";

    indice[residente] ??= {};
    indice[residente][anio] ??= {};
    indice[residente][anio][mes] ??= {};
    indice[residente][anio][mes][dia] ??= { manana: [], tarde: [], noche: [] };
    indice[residente][anio][mes][dia][turno].push(inc);
  }

  return indice;
}

function TarjetaIncidencia({ inc }) {
  const casos = inc.casos_reincidencia_json ? JSON.parse(inc.casos_reincidencia_json) : [];

  return (
    <li className="tarjeta-incidencia">
      <div className="tarjeta-cabecera">
        <span className="etiqueta-urgencia" style={{ backgroundColor: COLOR_URGENCIA[inc.urgencia] }}>
          {inc.urgencia}
        </span>
        <span className="tarjeta-fecha">{inc.proveedor}</span>
        {Boolean(inc.es_reincidencia) && <span className="etiqueta-reincidencia">⚠ Reincidencia</span>}
      </div>
      <p className="tarjeta-texto">{inc.texto_original}</p>
      <p className="tarjeta-detalle"><strong>{inc.categoria}</strong></p>
      <p className="tarjeta-razonamiento">{inc.razonamiento}</p>

      {casos.length > 0 && (
        <div className="aviso-reincidencia">
          {casos.length} incidencia(s) similar(es) previa(s):
          <ul>
            {casos.map((c, i) => (
              <li key={i}>
                {formatearFechaCorta(c.fecha?.split("T")[0] || c.fecha)} — {c.texto} (similitud {c.similitud})
              </li>
            ))}
          </ul>
        </div>
      )}
    </li>
  );
}

function FilaNavegacion({ opciones, seleccionado, onSeleccionar, etiquetaFn }) {
  return (
    <div className="fila-navegacion">
      {opciones.map((op) => (
        <button
          key={op}
          className={seleccionado === op ? "boton-nivel activo" : "boton-nivel"}
          onClick={() => onSeleccionar(op === seleccionado ? null : op)}
        >
          {etiquetaFn ? etiquetaFn(op) : op}
        </button>
      ))}
    </div>
  );
}

function NavegacionResidente({ datosPorAnio }) {
  const [anioSel, setAnioSel] = useState(null);
  const [mesSel, setMesSel] = useState(null);
  const [diaSel, setDiaSel] = useState(null);

  const anios = Object.keys(datosPorAnio).sort((a, b) => b.localeCompare(a));
  const meses = anioSel ? Object.keys(datosPorAnio[anioSel]).sort((a, b) => b.localeCompare(a)) : [];
  const dias = anioSel && mesSel ? Object.keys(datosPorAnio[anioSel][mesSel]).sort((a, b) => b.localeCompare(a)) : [];
  const datosDelDia = anioSel && mesSel && diaSel ? datosPorAnio[anioSel][mesSel][diaSel] : null;

  return (
    <div className="navegacion-residente">
      <FilaNavegacion
        opciones={anios}
        seleccionado={anioSel}
        onSeleccionar={(v) => { setAnioSel(v); setMesSel(null); setDiaSel(null); }}
      />

      {anioSel && (
        <FilaNavegacion
          opciones={meses}
          seleccionado={mesSel}
          onSeleccionar={(v) => { setMesSel(v); setDiaSel(null); }}
          etiquetaFn={(m) => NOMBRES_MES[parseInt(m, 10) - 1]}
        />
      )}

      {anioSel && mesSel && (
        <FilaNavegacion
          opciones={dias}
          seleccionado={diaSel}
          onSeleccionar={setDiaSel}
          etiquetaFn={(d) => `Día ${d}`}
        />
      )}

      {datosDelDia && (
        <div className="detalle-dia">
          {TURNOS_ORDENADOS.map((turno) => (
            <div key={turno} className="bloque-turno">
              <h5>{NOMBRE_TURNO[turno]}</h5>
              {datosDelDia[turno].length === 0 ? (
                <p className="sin-incidencias-turno">Sin incidencias en este turno.</p>
              ) : (
                <ul className="lista-incidencias">
                  {datosDelDia[turno].map((inc) => (
                    <TarjetaIncidencia key={inc.id} inc={inc} />
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function LibroIncidencias() {
  const [incidencias, setIncidencias] = useState([]);
  const [residentes, setResidentes] = useState([]);
  const [filtroResidente, setFiltroResidente] = useState("");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  async function cargarLibro(residenteId) {
    setCargando(true);
    setError(null);
    try {
      const datos = await obtenerLibro(residenteId);
      setIncidencias(datos);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    obtenerResidentes().then(setResidentes).catch(() => {});
    cargarLibro("");
  }, []);

  function manejarCambioFiltro(e) {
    const nuevoValor = e.target.value;
    setFiltroResidente(nuevoValor);
    cargarLibro(nuevoValor);
  }

  const indice = construirIndice(incidencias);

  return (
    <div>
      <h2>Libro de Incidencias</h2>

      <div className="filtro-libro">
        <select value={filtroResidente} onChange={manejarCambioFiltro}>
          <option value="">Todas las habitaciones</option>
          {residentes.map((r) => (
            <option key={r.id} value={r.id}>
              Habitación {r.habitacion}
            </option>
          ))}
        </select>
        <button onClick={() => cargarLibro(filtroResidente)}>Actualizar</button>
      </div>

      {cargando && <p>Cargando...</p>}
      {error && <p className="error">Error: {error}</p>}

      {!cargando && !error && incidencias.length === 0 && (
        <p>No hay incidencias registradas todavía.</p>
      )}

      {Object.entries(indice).map(([residente, datosPorAnio]) => (
        <div key={residente} className="grupo-residente">
          <h3>{residente}</h3>
          <NavegacionResidente datosPorAnio={datosPorAnio} />
        </div>
      ))}
    </div>
  );
}

export default LibroIncidencias;