import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { Card, Stat, Badge, Empty, formatCurrency, formatDateTime, formatCnpj } from "../components/ui.jsx";

const statusColor = {
  sucesso: "green",
  erro: "red",
  processando: "blue",
  pendente: "amber",
};

const certColor = {
  ok: "green",
  atencao: "amber",
  vencido: "red",
  desconhecido: "gray",
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentes, setRecentes] = useState([]);
  const [certs, setCerts] = useState([]);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    Promise.all([api.dashStats(), api.dashRecentes(), api.dashCertificados()])
      .then(([s, r, c]) => {
        setStats(s);
        setRecentes(r);
        setCerts(c);
      })
      .catch((e) => setErro(e.message));
  }, []);

  if (erro) return <Empty message={`Erro: ${erro}`} />;
  if (!stats) return <Empty message="Carregando painel…" />;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Painel CUBO Captura</h1>
        <p style={{ margin: "4px 0 0", color: "var(--cubo-muted)", fontSize: 13 }}>
          Visão geral da captura de XMLs NFS-e via GISS Maceió.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16 }}>
        <Stat label="Clientes ativos" value={stats.clientes_ativos} hint={`${stats.total_clientes} cadastrados`} />
        <Stat label="NFS-e no mês" value={stats.nfse_mes_atual} hint={`${stats.total_nfse} totais`} />
        <Stat label="Faturamento do mês" value={formatCurrency(stats.valor_mes_atual)} accent="var(--cubo-green)" />
        <Stat
          label="Consultas (7d)"
          value={stats.consultas_semana}
          hint={`${stats.consultas_erro_semana} com erro`}
          accent={stats.consultas_erro_semana > 0 ? "var(--cubo-amber)" : undefined}
        />
      </div>

      {stats.certificados_vencendo_30d > 0 && (
        <Card
          style={{
            background: "#fef3c7",
            border: "1px solid #fbbf24",
          }}
        >
          <div style={{ fontWeight: 600, color: "#92400e" }}>
            {stats.certificados_vencendo_30d} certificado(s) vencendo em até 30 dias.
          </div>
        </Card>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
        <Card title="Últimas consultas">
          {recentes.length === 0 ? (
            <Empty message="Nenhuma consulta recente" />
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Tipo</th>
                  <th>Notas</th>
                  <th>Status</th>
                  <th>Quando</th>
                </tr>
              </thead>
              <tbody>
                {recentes.map((r) => (
                  <tr key={r.consulta_id}>
                    <td>
                      <div style={{ fontWeight: 500 }}>{r.cliente}</div>
                      <div style={{ fontSize: 11, color: "var(--cubo-muted)" }}>{formatCnpj(r.cnpj)}</div>
                    </td>
                    <td style={{ fontSize: 12 }}>{r.tipo}</td>
                    <td>{r.total_notas}</td>
                    <td>
                      <Badge color={statusColor[r.status] || "gray"}>{r.status}</Badge>
                    </td>
                    <td style={{ fontSize: 12, color: "var(--cubo-muted)" }}>{formatDateTime(r.criado_em)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card title="Status dos certificados">
          {certs.length === 0 ? (
            <Empty message="Nenhum certificado cadastrado" />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {certs.slice(0, 6).map((c) => (
                <div
                  key={c.cliente_id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    paddingBottom: 12,
                    borderBottom: "1px solid var(--cubo-border)",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 500, fontSize: 13 }}>{c.razao_social}</div>
                    <div style={{ fontSize: 11, color: "var(--cubo-muted)" }}>
                      Vence em {c.validade || "—"}
                    </div>
                  </div>
                  <Badge color={certColor[c.status] || "gray"}>
                    {c.dias_para_vencer != null ? `${c.dias_para_vencer}d` : c.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
