import { useState } from "react";
import "./App.css";
import TriajeIndividual from "./components/TriajeIndividual";
import ComparacionProveedores from "./components/ComparacionProveedores";
import LibroIncidencias from "./components/LibroIncidencias";
import AdministracionPersonal from "./components/AdministracionPersonal";
import CambiarPasswordObligatorio from "./components/CambiarPasswordObligatorio";
import RecuperarPassword from "./components/RecuperarPassword";
import { login } from "./api";

function PantallaLogin({ onLoginExitoso, onIrARecuperar }) {
  const [usuario, setUsuario] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);

  async function manejarEnvio(e) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const persona = await login(usuario.trim(), password);
      onLoginExitoso(persona, password);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="pantalla-identificacion">
      <h2>Iniciar sesión</h2>
      <form onSubmit={manejarEnvio} className="formulario-triaje">
        <label>
          Usuario
          <input type="text" value={usuario} onChange={(e) => setUsuario(e.target.value)} placeholder="ej. aaranguez" required />
        </label>
        <label>
          Contraseña
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={cargando}>{cargando ? "Entrando..." : "Entrar"}</button>
      </form>
      <button className="boton-cambiar-usuario" onClick={onIrARecuperar}>¿Olvidaste tu contraseña?</button>
    </div>
  );
}

function App() {
  const [pestanaActiva, setPestanaActiva] = useState("individual");
  const [vista, setVista] = useState("login");
  const [usuario, setUsuario] = useState(() => {
    const guardado = localStorage.getItem("resicare_usuario");
    return guardado ? JSON.parse(guardado) : null;
  });
  const [passwordTemporal, setPasswordTemporal] = useState("");

  function manejarLoginExitoso(persona, passwordUsada) {
    if (persona.debe_cambiar_password) {
      setPasswordTemporal(passwordUsada);
      setUsuario(persona);
      setVista("cambiar_password");
    } else {
      localStorage.setItem("resicare_usuario", JSON.stringify(persona));
      setUsuario(persona);
      setVista("app");
    }
  }

  function manejarCambioCompletado() {
    const actualizado = { ...usuario, debe_cambiar_password: false };
    localStorage.setItem("resicare_usuario", JSON.stringify(actualizado));
    setUsuario(actualizado);
    setVista("app");
  }

  function cerrarSesion() {
    localStorage.removeItem("resicare_usuario");
    setUsuario(null);
    setVista("login");
    setPestanaActiva("individual");
  }

  const yaLogueado = usuario && localStorage.getItem("resicare_usuario");

  if (!yaLogueado || vista !== "app") {
    let contenido;
    if (vista === "cambiar_password" && usuario) {
      contenido = (
        <CambiarPasswordObligatorio
          usuario={usuario.usuario}
          passwordActual={passwordTemporal}
          onCompletado={manejarCambioCompletado}
        />
      );
    } else if (vista === "recuperar") {
      contenido = (
        <RecuperarPassword
          onVolver={() => setVista("login")}
          onRestablecido={() => setVista("login")}
        />
      );
    } else {
      contenido = (
        <PantallaLogin
          onLoginExitoso={manejarLoginExitoso}
          onIrARecuperar={() => setVista("recuperar")}
        />
      );
    }

    return (
      <div className="layout">
        <div className="contenido-principal">
          <div className="app">
            <header className="cabecera">
              <h1>ResiCare</h1>
              <p>Motor de triaje inteligente</p>
            </header>
            {contenido}
          </div>
        </div>
        <aside className="panel-lateral">
          <img src="/img/1.avif" alt="Residente paseando acompañado por un jardín" />
        </aside>
      </div>
    );
  }

  const esAdmin = usuario.rol === "administrador";

  return (
    <div className="layout">
      <div className="contenido-principal">
        <div className="app">
          <header className="cabecera">
            <span className="hoja hoja-1">🍃</span>
            <span className="hoja hoja-2">🍃</span>
            <span className="hoja hoja-3">🍃</span>
            <h1>ResiCare</h1>
            <p>
              Motor de triaje inteligente · Conectado como <strong>{usuario.nombre}</strong>
              {" "}
              <button className="boton-cambiar-usuario" onClick={cerrarSesion}>(cerrar sesión)</button>
            </p>
          </header>

          <nav className="pestanas">
            <button className={pestanaActiva === "individual" ? "activa" : ""} onClick={() => setPestanaActiva("individual")}>
              Triaje individual
            </button>
            <button className={pestanaActiva === "comparar" ? "activa" : ""} onClick={() => setPestanaActiva("comparar")}>
              Comparar proveedores
            </button>
            <button className={pestanaActiva === "libro" ? "activa" : ""} onClick={() => setPestanaActiva("libro")}>
              Libro de Incidencias
            </button>
            {esAdmin && (
              <button className={pestanaActiva === "administracion" ? "activa" : ""} onClick={() => setPestanaActiva("administracion")}>
                Administración
              </button>
            )}
          </nav>

          <main>
            {pestanaActiva === "individual" && <TriajeIndividual usuario={usuario.nombre} />}
            {pestanaActiva === "comparar" && <ComparacionProveedores />}
            {pestanaActiva === "libro" && <LibroIncidencias />}
            {pestanaActiva === "administracion" && esAdmin && <AdministracionPersonal />}
          </main>

          <footer className="pie-pagina">
            <p>ResiCare — desarrollado por <strong>Adriana Aránguez García</strong></p>
            <p>
              <a href="https://github.com/adrianaarang/ResiCare" target="_blank" rel="noopener noreferrer">Repositorio en GitHub</a>
              {" · "}
              Foto de <a href="https://unsplash.com/es" target="_blank" rel="noopener noreferrer">Unsplash</a>
            </p>
          </footer>
        </div>
      </div>

      <aside className="panel-lateral">
        <img src="/img/1.avif" alt="Residente paseando acompañado por un jardín" />
      </aside>
    </div>
  );
}

export default App;