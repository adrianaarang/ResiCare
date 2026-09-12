import { useState } from "react";
import { cambiarPassword } from "../api";

function CambiarPasswordObligatorio({ usuario, passwordActual, onCompletado }) {
  const [passwordNueva, setPasswordNueva] = useState("");
  const [passwordNueva2, setPasswordNueva2] = useState("");
  const [preguntaSecreta, setPreguntaSecreta] = useState("");
  const [respuestaSecreta, setRespuestaSecreta] = useState("");
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);

  async function manejarEnvio(e) {
    e.preventDefault();
    setError(null);

    if (passwordNueva.length < 6) {
      setError("La contraseña nueva debe tener al menos 6 caracteres.");
      return;
    }
    if (passwordNueva !== passwordNueva2) {
      setError("Las dos contraseñas nuevas no coinciden.");
      return;
    }
    if (!preguntaSecreta.trim() || !respuestaSecreta.trim()) {
      setError("Debes rellenar la pregunta y la respuesta secreta.");
      return;
    }

    setCargando(true);
    try {
      await cambiarPassword({
        usuario,
        passwordActual,
        passwordNueva,
        preguntaSecreta: preguntaSecreta.trim(),
        respuestaSecreta: respuestaSecreta.trim(),
      });
      onCompletado(passwordNueva);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="pantalla-identificacion">
      <h2>Cambia tu contraseña</h2>
      <p className="descripcion-comparar">
        Es tu primer acceso: debes establecer una contraseña nueva y una
        pregunta secreta (para poder recuperarla si la olvidas).
      </p>

      <form onSubmit={manejarEnvio} className="formulario-triaje">
        <label>
          Contraseña nueva
          <input type="password" value={passwordNueva} onChange={(e) => setPasswordNueva(e.target.value)} required />
        </label>
        <label>
          Repite la contraseña nueva
          <input type="password" value={passwordNueva2} onChange={(e) => setPasswordNueva2(e.target.value)} required />
        </label>
        <label>
          Pregunta secreta
          <input
            type="text"
            value={preguntaSecreta}
            onChange={(e) => setPreguntaSecreta(e.target.value)}
            placeholder="Ej: ¿Nombre de tu primera mascota?"
            required
          />
        </label>
        <label>
          Respuesta secreta
          <input type="text" value={respuestaSecreta} onChange={(e) => setRespuestaSecreta(e.target.value)} required />
        </label>

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={cargando}>
          {cargando ? "Guardando..." : "Guardar y entrar"}
        </button>
      </form>
    </div>
  );
}

export default CambiarPasswordObligatorio;