// Cliente HTTP do backend CUBO Captura
const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
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
  // Clientes
  listarClientes: () => request("/api/clientes"),
  criarCliente: (data) =>
    request("/api/clientes", { method: "POST", body: JSON.stringify(data) }),
  atualizarCliente: (id, data) =>
    request(`/api/clientes/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deletarCliente: (id) => request(`/api/clientes/${id}`, { method: "DELETE" }),

  uploadCertificado: async (id, arquivo, senha) => {
    const fd = new FormData();
    fd.append("arquivo", arquivo);
    fd.append("senha", senha);
    const res = await fetch(`${BASE}/api/clientes/${id}/certificado`, {
      method: "POST",
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
