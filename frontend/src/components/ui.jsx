import React from "react";

export const Card = ({ title, children, actions, style }) => (
  <div
    style={{
      background: "var(--cubo-surface)",
      borderRadius: 12,
      padding: 20,
      boxShadow: "0 1px 3px rgba(15,27,45,0.06)",
      border: "1px solid var(--cubo-border)",
      ...style,
    }}
  >
    {(title || actions) && (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        {title && <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>{title}</h3>}
        {actions}
      </div>
    )}
    {children}
  </div>
);

export const Stat = ({ label, value, hint, accent }) => (
  <Card>
    <div style={{ fontSize: 12, color: "var(--cubo-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
      {label}
    </div>
    <div style={{ fontSize: 28, fontWeight: 700, color: accent || "var(--cubo-dark)", marginTop: 6 }}>{value}</div>
    {hint && <div style={{ fontSize: 12, color: "var(--cubo-muted)", marginTop: 4 }}>{hint}</div>}
  </Card>
);

export const Button = ({ variant = "primary", children, ...props }) => {
  const base = {
    padding: "8px 16px",
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 500,
    cursor: "pointer",
    border: "1px solid transparent",
    transition: "all 150ms",
  };
  const variants = {
    primary: { background: "var(--cubo-blue)", color: "#fff" },
    accent: { background: "var(--cubo-accent)", color: "var(--cubo-dark)" },
    ghost: { background: "transparent", color: "var(--cubo-blue)", border: "1px solid var(--cubo-border)" },
    danger: { background: "var(--cubo-red)", color: "#fff" },
  };
  return (
    <button style={{ ...base, ...variants[variant] }} {...props}>
      {children}
    </button>
  );
};

export const Input = (props) => (
  <input
    {...props}
    style={{
      padding: "8px 12px",
      border: "1px solid var(--cubo-border)",
      borderRadius: 8,
      outline: "none",
      width: "100%",
      background: "#fff",
      ...props.style,
    }}
  />
);

export const Select = (props) => (
  <select
    {...props}
    style={{
      padding: "8px 12px",
      border: "1px solid var(--cubo-border)",
      borderRadius: 8,
      outline: "none",
      width: "100%",
      background: "#fff",
      ...props.style,
    }}
  />
);

export const Label = ({ children, style }) => (
  <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--cubo-muted)", marginBottom: 4, ...style }}>
    {children}
  </label>
);

export const Badge = ({ color = "gray", children }) => {
  const colors = {
    gray: { bg: "#e5e7eb", fg: "#374151" },
    green: { bg: "#d1fae5", fg: "#065f46" },
    amber: { bg: "#fef3c7", fg: "#92400e" },
    red: { bg: "#fee2e2", fg: "#991b1b" },
    blue: { bg: "#dbeafe", fg: "#1e40af" },
  };
  const c = colors[color] || colors.gray;
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 600,
        background: c.bg,
        color: c.fg,
        textTransform: "uppercase",
        letterSpacing: "0.03em",
      }}
    >
      {children}
    </span>
  );
};

export const Empty = ({ message = "Nenhum resultado" }) => (
  <div style={{ padding: 32, textAlign: "center", color: "var(--cubo-muted)", fontSize: 13 }}>{message}</div>
);

export const formatCurrency = (v) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(v || 0));

export const formatDate = (v) => (v ? new Date(v).toLocaleDateString("pt-BR") : "—");

export const formatDateTime = (v) => (v ? new Date(v).toLocaleString("pt-BR") : "—");

export const formatCnpj = (c) => {
  if (!c) return "";
  const d = String(c).padStart(14, "0");
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
};
