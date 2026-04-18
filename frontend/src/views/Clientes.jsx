import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { Card, Button, Input, Label, Badge, Empty, formatCnpj, formatDate } from "../components/ui.jsx";

export default function Clientes() {
  const [clientes, setClientes] = useState([]);
  const [novo, setNovo] = useState({ cnpj: "", inscricao_municipal: "", razao_social: "", nome_fantasia: "" });
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState(null);
  const [upload, setUpload] = useState({ clienteId: null, senha: "", arquivo: null });

  const load = () => api.listarClientes().then(setClientes).catch((e) => setErro(e.message));

  useEffect(() => {
    load();
  }, []);

  const criar = async (e) => {
    e.preventDefault();
    setErro(null);
    setCarregando(true);
    try {
      await api.criarCliente(novo);
      setNovo({ cnpj: "", inscricao_municipal: "", razao_social: "", nome_fantasia: "" });
      await load();
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  };

  const enviarCert = async (e) => {
    e.preventDefault();
    if (!upload.arquivo) return;
    setErro(null);
    setCarregando(true);
    try {
      await api.uploadCertificado(upload.clienteId, upload.arquivo, upload.senha);
      setUpload({ clienteId: null, senha: "", arquivo: null });
      await load();
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
    }
  };

  const remover = async (id) => {
    if (!confirm("Remover este cliente?")) return;
    try {
      await api.deletarCliente(id);
      await load();
    } catch (e) {
      setErro(e.message);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Clientes</h1>
        <p style={{ margin: "4px 0 0", color: "var(--cubo-muted)", fontSize: 13 }}>
          Cadastro de prestadores e seus certificados A1.
        </p>
      </div>

      {erro && (
        <Card style={{ background: "#fee2e2", border: "1px solid #fca5a5" }}>
          <div style={{ color: "#991b1b", fontSize: 13 }}>{erro}</div>
        </Card>
      )}

      <Card title="Novo cliente">
        <form onSubmit={criar} style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, alignItems: "end" }}>
          <div>
            <Label>CNPJ</Label>
            <Input
              required
              value={novo.cnpj}
              onChange={(e) => setNovo({ ...novo, cnpj: e.target.value })}
              placeholder="00000000000000"
            />
          </div>
          <div>
            <Label>Inscrição municipal</Label>
            <Input
              required
              value={novo.inscricao_municipal}
              onChange={(e) => setNovo({ ...novo, inscricao_municipal: e.target.value })}
            />
          </div>
          <div>
            <Label>Razão social</Label>
            <Input
              required
              value={novo.razao_social}
              onChange={(e) => setNovo({ ...novo, razao_social: e.target.value })}
            />
          </div>
          <div>
            <Label>Nome fantasia</Label>
            <Input value={novo.nome_fantasia} onChange={(e) => setNovo({ ...novo, nome_fantasia: e.target.value })} />
          </div>
          <Button type="submit" disabled={carregando} style={{ gridColumn: "span 4", justifySelf: "start" }}>
            {carregando ? "Salvando…" : "Cadastrar cliente"}
          </Button>
        </form>
      </Card>

      <Card title={`Clientes (${clientes.length})`}>
        {clientes.length === 0 ? (
          <Empty />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Razão social</th>
                <th>CNPJ</th>
                <th>IM</th>
                <th>Certificado</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {clientes.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{c.razao_social}</div>
                    {c.nome_fantasia && <div style={{ fontSize: 11, color: "var(--cubo-muted)" }}>{c.nome_fantasia}</div>}
                  </td>
                  <td style={{ fontSize: 12 }}>{formatCnpj(c.cnpj)}</td>
                  <td style={{ fontSize: 12 }}>{c.inscricao_municipal}</td>
                  <td style={{ fontSize: 12 }}>
                    {c.cert_path ? (
                      <>
                        <Badge color="green">OK</Badge>
                        <div style={{ fontSize: 11, color: "var(--cubo-muted)", marginTop: 2 }}>
                          Vence {formatDate(c.cert_validade)}
                        </div>
                      </>
                    ) : (
                      <Badge color="amber">Sem certificado</Badge>
                    )}
                  </td>
                  <td>
                    <Badge color={c.ativo ? "green" : "gray"}>{c.ativo ? "Ativo" : "Inativo"}</Badge>
                  </td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    <Button variant="ghost" onClick={() => setUpload({ clienteId: c.id, senha: "", arquivo: null })}>
                      Certificado
                    </Button>{" "}
                    <Button variant="danger" onClick={() => remover(c.id)}>
                      Remover
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {upload.clienteId && (
        <Card title="Upload de certificado A1 (.pfx)">
          <form onSubmit={enviarCert} style={{ display: "grid", gridTemplateColumns: "2fr 1fr auto", gap: 12, alignItems: "end" }}>
            <div>
              <Label>Arquivo .pfx / .p12</Label>
              <input
                type="file"
                accept=".pfx,.p12"
                required
                onChange={(e) => setUpload({ ...upload, arquivo: e.target.files[0] })}
              />
            </div>
            <div>
              <Label>Senha do certificado</Label>
              <Input
                type="password"
                required
                value={upload.senha}
                onChange={(e) => setUpload({ ...upload, senha: e.target.value })}
              />
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <Button type="submit" variant="accent" disabled={carregando}>
                {carregando ? "Enviando…" : "Enviar"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setUpload({ clienteId: null, senha: "", arquivo: null })}>
                Cancelar
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
