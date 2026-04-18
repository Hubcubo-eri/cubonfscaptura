import React from "react";

const NAV = [
  { key: "dashboard", label: "Painel" },
  { key: "clientes", label: "Clientes" },
  { key: "consultas", label: "Consultas" },
  { key: "nfse", label: "NFS-e" },
];

export default function Layout({ view, onNavigate, children }) {
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
                borderLeft: view === item.key ? "3px solid var(--cubo-accent)" : "3px solid transparent",
                cursor: "pointer",
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div style={{ padding: "16px 24px", fontSize: 11, color: "#64748b", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
          v1.0.0 · GISS Maceió
        </div>
      </aside>
      <main style={{ flex: 1, padding: 32, overflow: "auto" }}>{children}</main>
    </div>
  );
}
