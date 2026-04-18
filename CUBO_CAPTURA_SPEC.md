# CUBO CAPTURA — Especificação Técnica v1.0
## Sistema de Captura de XML NFS-e via Web Service GISS Maceió

---

## 1. Visão Geral

Aplicação web para captura automatizada de XMLs de Notas Fiscais de Serviço Eletrônicas (NFS-e) emitidas pelos clientes da Cubo Saúde no município de Maceió/AL, via Web Service SOAP do sistema GISS Online.

### Stack Tecnológica
- **Backend:** Python 3.11+ / FastAPI
- **Frontend:** React (Vite) + Tailwind-free (inline styles com design system Cubo)
- **Banco de Dados:** PostgreSQL (prod) / SQLite (dev)
- **ORM:** SQLAlchemy + Alembic (migrations)
- **Cliente SOAP:** zeep + lxml
- **Assinatura XML:** signxml + cryptography
- **Certificados:** pyOpenSSL (leitura .pfx)
- **Task Queue:** Celery + Redis (agendamentos)
- **Storage XMLs:** Filesystem organizado (ou S3 futuro)

---

## 2. Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│  Dashboard · Clientes · Consultas · Histórico · Upload   │
└────────────────────────┬────────────────────────────────┘
                         │ REST API (JSON)
┌────────────────────────▼────────────────────────────────┐
│                  Backend (FastAPI)                        │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ API REST │  │ SOAP     │  │ Celery   │               │
│  │ Routes   │  │ Client   │  │ Workers  │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       │             │             │                      │
│  ┌────▼─────────────▼─────────────▼─────┐               │
│  │        Core Services                  │               │
│  │  · CertificadoService                │               │
│  │  · GISSClientService                 │               │
│  │  · XMLSignerService                  │               │
│  │  · ConsultaService                   │               │
│  │  · StorageService                    │               │
│  └────┬──────────────────────────┬──────┘               │
│       │                          │                      │
│  ┌────▼──────┐           ┌───────▼──────┐               │
│  │ PostgreSQL│           │  Filesystem  │               │
│  │ (metadata)│           │  (XMLs .pfx) │               │
│  └───────────┘           └──────────────┘               │
└─────────────────────────────────────────────────────────┘
                         │ SOAP/TLS 1.2
                         ▼
              ┌─────────────────────┐
              │   GISS Maceió WS    │
              │  ws-maceio.giss.    │
              │  com.br             │
              └─────────────────────┘
```

---

## 3. Roadmap

### Fase 1 — MVP
- [x] Especificação técnica
- [x] Estrutura do projeto (backend + frontend + docker)
- [x] Backend FastAPI + modelos
- [x] Módulo GISS (client SOAP, signer, parser, builder)
- [x] CRUD clientes + upload cert
- [x] Consulta manual (período + faixa)
- [x] Download XML individual/ZIP
- [x] Frontend dashboard (React)

### Fase 2 — Automação
- [x] Celery + Redis (agendamentos)
- [x] Alertas persistidos (certificado vencendo, falhas)
- [x] Tela de alertas no frontend

### Fase 3 — Multi-município
- [ ] Suporte a outros municípios GISS
- [ ] Configuração dinâmica de WSDL
- [ ] Painel de municípios suportados

Para detalhes de modelos, endpoints e implementação, ver README.md e código-fonte.
