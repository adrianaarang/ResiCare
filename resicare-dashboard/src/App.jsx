import { useState } from "react";
import "./App.css";
import TriajeIndividual from "./components/TriajeIndividual";
import ComparacionProveedores from "./components/ComparacionProveedores";
import LibroIncidencias from "./components/LibroIncidencias";

function App() {
  const [pestanaActiva, setPestanaActiva] = useState("individual");

  return (
    <div className="app">
      <header className="cabecera">
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
      </main>
    </div>
  );
}

export default App;
