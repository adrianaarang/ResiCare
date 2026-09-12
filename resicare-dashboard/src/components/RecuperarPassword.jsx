import { useState } from "react";
import { obtenerPreguntaSecreta, restablecerPassword } from "../api";

function RecuperarPassword({ onVolver, onRestablecido }) {
  const [paso, setPaso] = useState(1);
  const [usuario, setUsuario] = useState("");
  const [pregunta, setPregunta] = useState("");
  const [respuesta, setRespuesta] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [passwordNueva2, setPasswordNueva2] = useState("");
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);

  async function buscarPregunta(e) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const p = await obtenerPreguntaSecreta(usuario.trim());
      setPregunta(p);
      setPaso(2);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  async function restablecer(e) {
    e.preventDefault();
    setError(null);

    if (passwordNueva.length < 6) {
      setError("La contraseña nueva debe tener al menos 6 caracteres.");
      return;
    }
    if (passwordNueva !== passwordNueva2) {
      setError("Las dos contraseñas no coinciden.");
      return;
    }

    setCargando(true);
    try {
      await restablecerPassword({ usuario: usuario.trim(), respuesta, passwordNueva });
      onRestablecido();
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="pantalla-identificacion">
      <h2>Recuperar contraseña</h2>

      {paso === 1 && (
        <form onSubmit={buscarPregunta} className="formulario-triaje">
          <label>
            Usuario
            <input type="text" value={usuario} onChange={(e) => setUsuario(e.target.value)} required />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={cargando}>{cargando ? "Buscando..." : "Continuar"}</button>
        </form>
      )}

      {paso === 2 && (
        <form onSubmit={restablecer} className="formulario-triaje">
          <p className="descripcion-comparar"><strong>{pregunta}</strong></p>
          <label>
            Tu respuesta
            <input type="text" value={respuesta} onChange={(e) => setRespuesta(e.target.value)} required />
          </label>
          <label>
            Contraseña nueva
            <input type="password" value={passwordNueva} onChange={(e) => setPasswordNueva(e.target.value)} required />
          </label>
          <label>
            Repite la contraseña nueva
            <input type="password" value={passwordNueva2} onChange={(e) => setPasswordNueva2(e.target.value)} required />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={cargando}>{cargando ? "Restableciendo..." : "Restablecer contraseña"}</button>
        </form>
      )}

      <button className="boton-cambiar-usuario" onClick={onVolver}>Volver al inicio de sesión</button>
    </div>
  );
}

export default RecuperarPassword;