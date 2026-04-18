import React from "react";

const NAV = [
  { key: "dashboard", label: "Painel" },
  { key: "clientes", label: "Clientes" },
  { key: "consultas", label: "Consultas" },
  { key: "nfse", label: "NFS-e" },
  { key: "alertas", label: "Alertas" },
];

export default function Layout({ view, onNavigate, children, user, onLogout }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 220,
          background: "var(--cubo-dark)",
          color: "#fff",
          padding: "24px 0",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "0 24px 24px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ fontWeight: 700, fontSize: 18, letterSpacing: "0.5px" }}>CUBO</div>
          <div style={{ fontSize: 12, color: "var(--cubo-accent)", marginTop: 2 }}>Captura NFS-e</div>
        </div>
        <nav style={{ flex: 1, paddingTop: 16 }}>
          {NAV.map((item) => (
            <button
              key={item.key}
              onClick={() => onNavigate(item.key)}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "12px 24px",
                background: view === item.key ? "rgba(34,211,238,0.12)" : "transparent",
                color: view === item.key ? "var(--cubo-accent)" : "#cbd5e1",
                border: "none",
                borderLeft:
                  view === item.key ? "3px solid var(--cubo-accent)" : "3px solid transparent",
                cursor: "pointer",
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>
        {user && (
          <div style={{ padding: "16px 24px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
            <div style={{ fontSize: 12, color: "#cbd5e1", marginBottom: 2 }}>{user.nome}</div>
            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 8 }}>{user.email}</div>
            <button
              onClick={onLogout}
              style={{
                background: "transparent",
                color: "var(--cubo-accent)",
                border: "1px solid rgba(34,211,238,0.3)",
                padding: "4px 10px",
                borderRadius: 6,
                fontSize: 11,
                cursor: "pointer",
              }}
            >
              Sair
            </button>
          </div>
        )}
        <div style={{ padding: "12px 24px", fontSize: 11, color: "#64748b" }}>v1.0.0</div>
      </aside>
      <main style={{ flex: 1, padding: 32, overflow: "auto" }}>{children}</main>
    </div>
  );
}
