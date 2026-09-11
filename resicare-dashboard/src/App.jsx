import { useState } from "react";
import "./App.css";
import TriajeIndividual from "./components/TriajeIndividual";
import ComparacionProveedores from "./components/ComparacionProveedores";
import LibroIncidencias from "./components/LibroIncidencias";

function App() {
  const [pestanaActiva, setPestanaActiva] = useState("individual");

  return (
    <div className="layout">
      <div className="contenido-principal">
        <div className="app">
          <header className="cabecera">
            <span className="hoja hoja-1">🍃</span>
            <span className="hoja hoja-2">🍃</span>
            <span className="hoja hoja-3">🍃</span>
            <h1>ResiCare</h1>
            <p>Motor de triaje inteligente</p>
          </header>

          <nav className="pestanas">
            <button
              className={pestanaActiva === "individual" ? "activa" : ""}
              onClick={() => setPestanaActiva("individual")}
            >
              Triaje individual
            </button>
            <button
              className={pestanaActiva === "comparar" ? "activa" : ""}
              onClick={() => setPestanaActiva("comparar")}
            >
              Comparar proveedores
            </button>
            <button
              className={pestanaActiva === "libro" ? "activa" : ""}
              onClick={() => setPestanaActiva("libro")}
            >
              Libro de Incidencias
            </button>
          </nav>

          <main>
            {pestanaActiva === "individual" && <TriajeIndividual />}
            {pestanaActiva === "comparar" && <ComparacionProveedores />}
            {pestanaActiva === "libro" && <LibroIncidencias />}
                      <footer className="pie-pagina">
            <p>
              ResiCare — desarrollado por <strong>Adriana Aránguez García</strong>
            </p>
            <p>
              <a href="https://github.com/adrianaarang/ResiCare" target="_blank" rel="noopener noreferrer">
                Repositorio en GitHub
              </a>
              {" · "}
              Foto de{" "}
              <a href="https://unsplash.com/es" target="_blank" rel="noopener noreferrer">
                Unsplash
              </a>
            </p>
          </footer>
          </main>
        </div>
      </div>

      <aside className="panel-lateral">
        <img src="/img/1.avif" alt="Residente paseando acompañado por un jardín" />
      </aside>
    </div>
  );
}

export default App;