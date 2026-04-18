// Cliente HTTP do backend CUBO Captura
import { auth } from "./auth.js";

const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = auth.getToken();
  if (token && !headers.Authorization) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    auth.clear();
    window.location.reload();
    throw new Error("Sessão expirada");
  }
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      detail = JSON.parse(text).detail || detail;
    } catch (_) {}
    throw new Error(detail || `Erro ${res.status}`);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

export const api = {
  // Auth
  login: async (email, password) => {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) {
      const t = await res.text();
      let detail = t;
      try {
        detail = JSON.parse(t).detail || detail;
      } catch (_) {}
      throw new Error(detail || "Falha no login");
    }
    const data = await res.json();
    auth.setToken(data.access_token);
    const me = await request("/api/auth/me");
    auth.setUser(me);
    return me;
  },
  logout: () => auth.clear(),
  me: () => request("/api/auth/me"),

  // Clientes
  listarClientes: () => request("/api/clientes"),
  criarCliente: (data) => request("/api/clientes", { method: "POST", body: JSON.stringify(data) }),
  atualizarCliente: (id, data) =>
    request(`/api/clientes/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deletarCliente: (id) => request(`/api/clientes/${id}`, { method: "DELETE" }),

  uploadCertificado: async (id, arquivo, senha) => {
    const fd = new FormData();
    fd.append("arquivo", arquivo);
    fd.append("senha", senha);
    const headers = {};
    const token = auth.getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${BASE}/api/clientes/${id}/certificado`, {
      method: "POST",
      headers,
      body: fd,
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(t || `Erro ${res.status}`);
    }
    return res.json();
  },
  infoCertificado: (id) => request(`/api/clientes/${id}/certificado`),

  // Consultas
  executarConsulta: (payload) =>
    request("/api/consultas", { method: "POST", body: JSON.stringify(payload) }),
  listarConsultas: (clienteId) =>
    request(`/api/consultas${clienteId ? `?cliente_id=${clienteId}` : ""}`),

  // NFS-e
  listarNfse: (filtros = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(filtros).filter(([, v]) => v))
    );
    return request(`/api/nfse?${qs}`);
  },
  statsNfse: (clienteId) =>
    request(`/api/nfse/stats${clienteId ? `?cliente_id=${clienteId}` : ""}`),
  downloadXmlUrl: (id) => `${BASE}/api/nfse/${id}/xml`,
  exportZipUrl: (filtros = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(filtros).filter(([, v]) => v))
    );
    return `${BASE}/api/nfse/export?${qs}`;
  },

  // Dashboard
  dashStats: () => request("/api/dashboard/stats"),
  dashRecentes: () => request("/api/dashboard/recentes"),
  dashCertificados: () => request("/api/dashboard/certificados"),

  // Alertas
  listarAlertas: (apenasAbertos = true) =>
    request(`/api/alertas?apenas_abertos=${apenasAbertos}`),
  resolverAlerta: (id) => request(`/api/alertas/${id}/resolver`, { method: "POST" }),
};
