import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { Card, Button, Badge, Empty, formatDateTime } from "../components/ui.jsx";

const severityColor = {
  critical: "red",
  warning: "amber",
  info: "blue",
};

export default function Alertas() {
  const [alertas, setAlertas] = useState([]);
  const [mostrarResolvidos, setMostrarResolvidos] = useState(false);
  const [erro, setErro] = useState(null);

  const load = () =>
    api
      .listarAlertas(!mostrarResolvidos)
      .then(setAlertas)
      .catch((e) => setErro(e.message));

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mostrarResolvidos]);

  const resolver = async (id) => {
    try {
      await api.resolverAlerta(id);
      load();
    } catch (e) {
      setErro(e.message);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Alertas</h1>
        <p style={{ margin: "4px 0 0", color: "var(--cubo-muted)", fontSize: 13 }}>
          Eventos operacionais (certificados vencendo, falhas de consulta).
        </p>
      </div>

      {erro && (
        <Card style={{ background: "#fee2e2", border: "1px solid #fca5a5" }}>
          <div style={{ color: "#991b1b", fontSize: 13 }}>{erro}</div>
        </Card>
      )}

      <Card
        title={`${alertas.length} ${mostrarResolvidos ? "alerta(s)" : "aberto(s)"}`}
        actions={
          <Button variant="ghost" onClick={() => setMostrarResolvidos(!mostrarResolvidos)}>
            {mostrarResolvidos ? "Ver apenas abertos" : "Incluir resolvidos"}
          </Button>
        }
      >
        {alertas.length === 0 ? (
          <Empty message="Nenhum alerta" />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Quando</th>
                <th>Tipo</th>
                <th>Severidade</th>
                <th>Mensagem</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {alertas.map((a) => (
                <tr key={a.id}>
                  <td style={{ fontSize: 12 }}>{formatDateTime(a.created_at)}</td>
                  <td style={{ fontSize: 12 }}>{a.tipo}</td>
                  <td>
                    <Badge color={severityColor[a.severity] || "gray"}>{a.severity}</Badge>
                  </td>
                  <td style={{ fontSize: 13 }}>{a.mensagem}</td>
                  <td>
                    <Badge color={a.resolvido ? "green" : "amber"}>
                      {a.resolvido ? "Resolvido" : "Aberto"}
                    </Badge>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {!a.resolvido && (
                      <Button variant="ghost" onClick={() => resolver(a.id)}>
                        Marcar resolvido
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
