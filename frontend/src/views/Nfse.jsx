import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { Card, Button, Input, Select, Label, Badge, Empty, formatCurrency, formatDate, formatCnpj } from "../components/ui.jsx";

export default function Nfse() {
  const [clientes, setClientes] = useState([]);
  const [filtros, setFiltros] = useState({ cliente_id: "", competencia_inicial: "", competencia_final: "" });
  const [notas, setNotas] = useState([]);
  const [stats, setStats] = useState(null);

  const buscar = async () => {
    const [lista, st] = await Promise.all([api.listarNfse(filtros), api.statsNfse(filtros.cliente_id)]);
    setNotas(lista);
    setStats(st);
  };

  useEffect(() => {
    api.listarClientes().then(setClientes);
    buscar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>NFS-e capturadas</h1>
        <p style={{ margin: "4px 0 0", color: "var(--cubo-muted)", fontSize: 13 }}>
          XMLs baixados do GISS Maceió — baixe individualmente ou exporte em lote.
        </p>
      </div>

      <Card title="Filtros">
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr auto auto", gap: 12, alignItems: "end" }}>
          <div>
            <Label>Cliente</Label>
            <Select value={filtros.cliente_id} onChange={(e) => setFiltros({ ...filtros, cliente_id: e.target.value })}>
              <option value="">Todos</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.razao_social}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Competência inicial</Label>
            <Input
              type="date"
              value={filtros.competencia_inicial}
              onChange={(e) => setFiltros({ ...filtros, competencia_inicial: e.target.value })}
            />
          </div>
          <div>
            <Label>Competência final</Label>
            <Input
              type="date"
              value={filtros.competencia_final}
              onChange={(e) => setFiltros({ ...filtros, competencia_final: e.target.value })}
            />
          </div>
          <Button onClick={buscar}>Filtrar</Button>
          <a href={api.exportZipUrl(filtros)} target="_blank" rel="noreferrer">
            <Button variant="accent">Exportar ZIP</Button>
          </a>
        </div>
      </Card>

      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16 }}>
          <Card>
            <div style={{ fontSize: 12, color: "var(--cubo-muted)" }}>Total NFS-e</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{stats.total_nfse}</div>
          </Card>
          <Card>
            <div style={{ fontSize: 12, color: "var(--cubo-muted)" }}>Valor serviços</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--cubo-green)" }}>
              {formatCurrency(stats.total_valor_servicos)}
            </div>
          </Card>
          <Card>
            <div style={{ fontSize: 12, color: "var(--cubo-muted)" }}>ISS recolhido</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{formatCurrency(stats.total_valor_iss)}</div>
          </Card>
          <Card>
            <div style={{ fontSize: 12, color: "var(--cubo-muted)" }}>Canceladas</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--cubo-red)" }}>{stats.total_canceladas}</div>
          </Card>
        </div>
      )}

      <Card title={`NFS-e (${notas.length})`}>
        {notas.length === 0 ? (
          <Empty message="Nenhuma NFS-e para os filtros selecionados" />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Número</th>
                <th>Emissão</th>
                <th>Competência</th>
                <th>Tomador</th>
                <th style={{ textAlign: "right" }}>Valor serviços</th>
                <th style={{ textAlign: "right" }}>ISS</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>XML</th>
              </tr>
            </thead>
            <tbody>
              {notas.map((n) => (
                <tr key={n.id}>
                  <td style={{ fontWeight: 500 }}>{n.numero_nfse}</td>
                  <td style={{ fontSize: 12 }}>{formatDate(n.data_emissao)}</td>
                  <td style={{ fontSize: 12 }}>{formatDate(n.competencia)}</td>
                  <td>
                    <div style={{ fontSize: 12 }}>{n.razao_social_tomador || "—"}</div>
                    {n.cnpj_tomador && (
                      <div style={{ fontSize: 11, color: "var(--cubo-muted)" }}>{formatCnpj(n.cnpj_tomador)}</div>
                    )}
                  </td>
                  <td style={{ textAlign: "right" }}>{formatCurrency(n.valor_servicos)}</td>
                  <td style={{ textAlign: "right" }}>{formatCurrency(n.valor_iss)}</td>
                  <td>
                    <Badge color={n.status_nfse === 1 ? "green" : "red"}>
                      {n.status_nfse === 1 ? "Normal" : "Cancelada"}
                    </Badge>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <a href={api.downloadXmlUrl(n.id)} target="_blank" rel="noreferrer">
                      <Button variant="ghost">Baixar</Button>
                    </a>
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
