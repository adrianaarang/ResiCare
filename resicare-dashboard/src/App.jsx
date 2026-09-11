import { useState } from "react";
import "./App.css";
import TriajeIndividual from "./components/TriajeIndividual";
import ComparacionProveedores from "./components/ComparacionProveedores";

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
      </nav>

      <main>
        {pestanaActiva === "individual" && <TriajeIndividual />}
        {pestanaActiva === "comparar" && <ComparacionProveedores />}
      </main>
    </div>
  );
}

export default App;