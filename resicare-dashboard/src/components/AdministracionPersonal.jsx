import { useState, useEffect } from "react";
import { obtenerPersonal, crearPersonal, eliminarPersonal } from "../api";

function AdministracionPersonal() {
  const [personal, setPersonal] = useState([]);
  const [nombre, setNombre] = useState("");
  const [rol, setRol] = useState("enfermera");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [altaCreada, setAltaCreada] = useState(null);

  async function cargar() {
    setCargando(true);
    setError(null);
    try {
      setPersonal(await obtenerPersonal());
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => { cargar(); }, []);

  async function manejarAlta(e) {
    e.preventDefault();
    if (!nombre.trim()) return;
    setAltaCreada(null);
    try {
      const nueva = await crearPersonal(nombre.trim(), rol);
      setAltaCreada(nueva);
      setNombre("");
      setRol("enfermera");
      cargar();
    } catch (e) {
      setError(e.message);
    }
  }

  async function manejarBaja(id, nombrePersona) {
    if (!window.confirm(`Dar de baja a ${nombrePersona}?`)) return;
    try {
      await eliminarPersonal(id);
      cargar();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <h2>Administracion de personal</h2>
      <p className="descripcion-comparar">
        Alta y baja de personal. Al dar de alta, se genera un usuario y una
        contrasena inicial que deberas comunicar a la persona (tendra que
        cambiarla en su primer acceso).
      </p>

      <form onSubmit={manejarAlta} className="formulario-triaje formulario-alta-personal">
        <label>
          Nombre
          <input type="text" value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Nombre completo" required />
        </label>
        <label>
          Rol
          <select value={rol} onChange={(e) => setRol(e.target.value)}>
            <option value="enfermera">Enfermera</option>
            <option value="administrador">Administrador</option>
          </select>
        </label>
        <button type="submit">Dar de alta</button>
      </form>

      {altaCreada && (
        <div className="aviso-reincidencia aviso-alta-creada">
          <strong>{altaCreada.nombre}</strong> dado de alta correctamente.<br />
          Usuario: <strong>{altaCreada.usuario}</strong> - Contrasena inicial: <strong>{altaCreada.password_inicial}</strong>
          <br />
          Comunicasela para que pueda entrar (debera cambiarla en su primer acceso).
        </div>
      )}

      {error && <p className="error">Error: {error}</p>}
      {cargando && <p>Cargando...</p>}

      <ul className="lista-personal">
        {personal.map((p) => (
          <li key={p.id} className="fila-personal">
            <span>{p.nombre} <span className="usuario-login">@{p.usuario}</span></span>
            <span className={`etiqueta-rol etiqueta-rol-${p.rol}`}>{p.rol}</span>
            <button className="boton-baja" onClick={() => manejarBaja(p.id, p.nombre)}>Dar de baja</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default AdministracionPersonal;
