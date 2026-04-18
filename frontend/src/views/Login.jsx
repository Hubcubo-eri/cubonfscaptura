import React, { useState } from "react";
import { api } from "../api.js";
import { Input, Button, Label } from "../components/ui.jsx";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(false);

  const entrar = async (e) => {
    e.preventDefault();
    setErro(null);
    setCarregando(true);
    try {
      const me = await api.login(email, password);
      onLogin(me);
    } catch (e) {
      setErro(e.message || "Falha no login");
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, var(--cubo-dark) 0%, var(--cubo-blue) 100%)",
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 16,
          padding: 40,
          boxShadow: "0 20px 60px rgba(0,0,0,0.25)",
          width: 380,
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "var(--cubo-dark)" }}>CUBO</div>
          <div style={{ fontSize: 13, color: "var(--cubo-accent)", marginTop: 2 }}>Captura NFS-e</div>
        </div>

        <form onSubmit={entrar} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <Label>E-mail</Label>
            <Input
              type="email"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="voce@cubosaude.com.br"
            />
          </div>
          <div>
            <Label>Senha</Label>
            <Input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {erro && (
            <div
              style={{
                padding: 10,
                background: "#fee2e2",
                color: "#991b1b",
                borderRadius: 8,
                fontSize: 13,
              }}
            >
              {erro}
            </div>
          )}

          <Button type="submit" disabled={carregando}>
            {carregando ? "Entrando…" : "Entrar"}
          </Button>
        </form>
      </div>
    </div>
  );
}
