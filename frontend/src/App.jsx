import React, { useState } from "react";
import Layout from "./components/Layout.jsx";
import Dashboard from "./views/Dashboard.jsx";
import Clientes from "./views/Clientes.jsx";
import Consultas from "./views/Consultas.jsx";
import Nfse from "./views/Nfse.jsx";

const VIEWS = {
  dashboard: Dashboard,
  clientes: Clientes,
  consultas: Consultas,
  nfse: Nfse,
};

export default function App() {
  const [view, setView] = useState("dashboard");
  const Component = VIEWS[view] || Dashboard;

  return (
    <Layout view={view} onNavigate={setView}>
      <Component />
    </Layout>
  );
}
