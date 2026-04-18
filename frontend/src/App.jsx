import React, { useEffect, useState } from "react";
import Layout from "./components/Layout.jsx";
import Dashboard from "./views/Dashboard.jsx";
import Clientes from "./views/Clientes.jsx";
import Consultas from "./views/Consultas.jsx";
import Nfse from "./views/Nfse.jsx";
import Alertas from "./views/Alertas.jsx";
import Login from "./views/Login.jsx";
import { auth } from "./auth.js";
import { api } from "./api.js";

const VIEWS = {
  dashboard: Dashboard,
  clientes: Clientes,
  consultas: Consultas,
  nfse: Nfse,
  alertas: Alertas,
};

export default function App() {
  const [view, setView] = useState("dashboard");
  const [user, setUser] = useState(auth.getUser());
  const [verificando, setVerificando] = useState(Boolean(auth.getToken()));

  useEffect(() => {
    if (!auth.getToken()) {
      setVerificando(false);
      return;
    }
    api
      .me()
      .then((me) => {
        auth.setUser(me);
        setUser(me);
      })
      .catch(() => {
        auth.clear();
        setUser(null);
      })
      .finally(() => setVerificando(false));
  }, []);

  if (verificando) return null;
  if (!user) return <Login onLogin={setUser} />;

  const handleLogout = () => {
    api.logout();
    setUser(null);
  };

  const Component = VIEWS[view] || Dashboard;
  return (
    <Layout view={view} onNavigate={setView} user={user} onLogout={handleLogout}>
      <Component />
    </Layout>
  );
}
