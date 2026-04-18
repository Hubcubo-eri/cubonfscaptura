import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { Card, Button, Input, Select, Label, Badge, Empty, formatDateTime } from "../components/ui.jsx";

const statusColor = {
  sucesso: "green",
  erro: "red",
  processando: "blue",
  pendente: "amber",
};

export default function Consultas() {
  const [clientes, setClientes] = useState([]);
  const [consultas, setConsultas] = useState([]);
  const [form, setForm] = useState({
    cliente_id: "",
    tipo: "periodo_emissao",
    data_inicial: "",
    data_final: "",
    nfse_inicial: "",
    nfse_final: "",
  });
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState(null);

  const load = () => api.listarConsultas().then(setConsultas);

  useEffect(() => {
    api.listarClientes().then(setClientes);
    load();
  }, []);

  const executar = async (e) => {
    e.preventDefault();
    setErro(null);
    setResultado(null);
    setEnviando(true);
    try {
      const params = {};
      if (form.tipo.startsWith("periodo")) {
        params.data_inicial = form.data_inicial;
        params.data_final = form.data_final;
      } else if (form.tipo === "faixa") {
        params.nfse_inicial = Number(form.nfse_inicial);
        params.nfse_final = Number(form.nfse_final);
      }
      const res = await api.executarConsulta({
        cliente_id: form.cliente_id,
        tipo: form.tipo,
        parametros: params,
      });
      setResultado(res);
      await load();
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Consultas</h1>
        <p style={{ margin: "4px 0 0", color: "var(--cubo-muted)", fontSize: 13 }}>
          Dispare consultas SOAP ao GISS Maceió e acompanhe o histórico.
        </p>
      </div>

      <Card title="Nova consulta">
        <form onSubmit={executar} style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, alignItems: "end" }}>
          <div style={{ gridColumn: "span 2" }}>
            <Label>Cliente</Label>
            <Select required value={form.cliente_id} onChange={(e) => setForm({ ...form, cliente_id: e.target.value })}>
              <option value="">Selecione…</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.razao_social} — {c.cnpj}
                </option>
              ))}
            </Select>
          </div>
          <div style={{ gridColumn: "span 2" }}>
            <Label>Tipo de consulta</Label>
            <Select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
              <option value="periodo_emissao">Período de emissão</option>
              <option value="periodo_competencia">Período de competência</option>
              <option value="faixa">Faixa de número NFS-e</option>
            </Select>
          </div>

          {form.tipo.startsWith("periodo") ? (
            <>
              <div>
                <Label>Data inicial</Label>
                <Input type="date" required value={form.data_inicial} onChange={(e) => setForm({ ...form, data_inicial: e.target.value })} />
              </div>
              <div>
                <Label>Data final</Label>
                <Input type="date" required value={form.data_final} onChange={(e) => setForm({ ...form, data_final: e.target.value })} />
              </div>
            </>
          ) : (
            <>
              <div>
                <Label>NFS-e inicial</Label>
                <Input type="number" required value={form.nfse_inicial} onChange={(e) => setForm({ ...form, nfse_inicial: e.target.value })} />
              </div>
              <div>
                <Label>NFS-e final</Label>
                <Input type="number" required value={form.nfse_final} onChange={(e) => setForm({ ...form, nfse_final: e.target.value })} />
              </div>
            </>
          )}

          <Button type="submit" variant="accent" disabled={enviando} style={{ gridColumn: "span 4", justifySelf: "start" }}>
            {enviando ? "Consultando GISS…" : "Executar consulta"}
          </Button>
        </form>

        {erro && (
          <div style={{ marginTop: 16, padding: 12, background: "#fee2e2", borderRadius: 8, color: "#991b1b", fontSize: 13 }}>
            {erro}
          </div>
        )}
        {resultado && (
          <div style={{ marginTop: 16, padding: 12, background: "#d1fae5", borderRadius: 8, fontSize: 13 }}>
            <div style={{ fontWeight: 600, color: "#065f46" }}>
              Consulta {resultado.status} — {resultado.total_notas} notas ({resultado.novos_xmls} novas) em{" "}
              {resultado.duracao_ms}ms.
            </div>
          </div>
        )}
      </Card>

      <Card title={`Histórico (${consultas.length})`}>
        {consultas.length === 0 ? (
          <Empty />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Quando</th>
                <th>Tipo</th>
                <th>Parâmetros</th>
                <th>Notas</th>
                <th>Duração</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {consultas.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontSize: 12 }}>{formatDateTime(c.created_at)}</td>
                  <td style={{ fontSize: 12 }}>{c.tipo}</td>
                  <td style={{ fontSize: 11, color: "var(--cubo-muted)" }}>
                    {c.parametros ? JSON.stringify(c.parametros) : "—"}
                  </td>
                  <td>{c.total_notas}</td>
                  <td style={{ fontSize: 12 }}>{c.duracao_ms ? `${c.duracao_ms}ms` : "—"}</td>
                  <td>
                    <Badge color={statusColor[c.status] || "gray"}>{c.status}</Badge>
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
