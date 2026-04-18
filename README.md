# CUBO Captura — NFS-e GISS Maceió

Sistema web para captura automatizada de XMLs de Notas Fiscais de Serviço
Eletrônicas (NFS-e) emitidas no município de **Maceió/AL** via Web Service SOAP
do sistema **GISS Online** (padrão ABRASF 2.04).

> Ver [`CUBO_CAPTURA_SPEC.md`](CUBO_CAPTURA_SPEC.md) para a especificação técnica.

## Stack

| Camada        | Tecnologia                                         |
|---------------|----------------------------------------------------|
| Backend       | Python 3.11 · FastAPI · SQLAlchemy 2 · Pydantic v2 |
| SOAP / XML    | zeep · lxml · signxml · cryptography               |
| Banco         | PostgreSQL 16 (prod) / SQLite (dev)                |
| Task queue    | Celery + Redis                                     |
| Frontend      | React 18 · Vite · JSX (sem Tailwind)               |
| Deploy        | Docker Compose · Nginx                             |

## Arquitetura (resumo)

```
React (Vite) ──► FastAPI (REST)
                  │
                  ├─ GISS SOAP client (zeep + mTLS TLS1.2)
                  │   └─ assina XML (signxml RSA-SHA1)
                  │
                  ├─ PostgreSQL (metadados)
                  └─ Filesystem (XMLs em storage/xmls/{cnpj}/{YYYY-MM}/)
```

## Quickstart (desenvolvimento)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edite .env e defina uma MASTER_KEY forte
uvicorn app.main:app --reload --port 8000
```

A API estará em `http://localhost:8000`. Docs: `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App em `http://localhost:3000` (proxy `/api` → backend).

## Quickstart (produção com Docker)

```bash
cp backend/.env.example backend/.env
# Edite backend/.env: MASTER_KEY, DATABASE_URL, etc.
export DB_PASSWORD="senha-forte-aqui"
docker compose up -d --build
# Aplica migrations no PostgreSQL:
docker compose exec backend alembic upgrade head
```

- Frontend: http://localhost:3000
- Backend / Swagger: http://localhost:8000/docs

## Migrations (Alembic)

Em dev com SQLite o schema é criado automaticamente no startup. Em produção
(PostgreSQL) use Alembic:

```bash
cd backend
alembic upgrade head                    # aplica migrations pendentes
alembic current                         # mostra versão atual
alembic revision --autogenerate -m "..." # gera nova migration a partir dos models
alembic downgrade -1                    # reverte uma versão
```

## Testes

```bash
cd backend
pytest -v
```

Cobre: crypto (AES-GCM), xml_builder (ABRASF 2.04), xml_parser (response +
erros + cancelamento), storage (hash, estrutura, ZIP).

## Fluxo de uso

1. **Cadastrar cliente** (aba Clientes): CNPJ, IM, razão social.
2. **Upload do certificado A1** (.pfx): o sistema valida a senha, extrai CN e
   validade, grava criptografado em `backend/storage/certificados/`.
3. **Executar consulta** (aba Consultas): selecione cliente + tipo
   (período de emissão/competência ou faixa) + período.
4. **XMLs são baixados automaticamente** do GISS, deduplicados por hash e
   salvos em `backend/storage/xmls/{cnpj}/{YYYY-MM}/nfse_{numero}.xml`.
5. **Listar/baixar NFS-e** (aba NFS-e): filtros, download individual ou ZIP.

## Endpoints REST

| Verbo   | Rota                                         | Descrição                     |
|---------|----------------------------------------------|-------------------------------|
| GET     | `/api/clientes`                              | Lista clientes                |
| POST    | `/api/clientes`                              | Cria cliente                  |
| POST    | `/api/clientes/{id}/certificado`             | Upload .pfx + senha           |
| POST    | `/api/consultas`                             | Dispara consulta GISS         |
| GET     | `/api/consultas`                             | Histórico de consultas        |
| GET     | `/api/nfse`                                  | Lista NFS-e (com filtros)     |
| GET     | `/api/nfse/{id}/xml`                         | Download XML individual       |
| GET     | `/api/nfse/export`                           | Download ZIP                  |
| GET     | `/api/dashboard/stats`                       | Cards do painel               |
| GET     | `/api/dashboard/certificados`                | Status dos certificados       |

Ver Swagger em `/docs` para schemas completos.

## Segurança

- Senhas de certificados cifradas em repouso com **AES-256-GCM**, chave
  derivada via SHA-256 da `MASTER_KEY` definida em `.env`.
- Arquivos `.pfx` gravados com permissão `0600`.
- Comunicação com GISS via **TLS 1.2** mínimo e máximo (mTLS com cert A1).
- Elementos proibidos (`X509SerialNumber`, `RSAKeyValue`, etc.) removidos da
  `<Signature>` antes do envio, conforme exigência do GISS.
- CORS restrito à lista em `ALLOWED_ORIGINS`.

## Estrutura

```
cubonfscaptura/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI + CORS + lifespan
│   │   ├── config.py / database.py
│   │   ├── models/                  # SQLAlchemy
│   │   ├── schemas/                 # Pydantic
│   │   ├── routers/                 # REST
│   │   ├── services/                # Lógica de negócio
│   │   │   ├── giss_client.py       # SOAP + mTLS
│   │   │   ├── xml_signer.py        # signxml + clean GISS
│   │   │   ├── certificado.py
│   │   │   ├── consulta.py          # Orquestração
│   │   │   ├── crypto.py            # AES-256-GCM
│   │   │   └── storage.py
│   │   ├── giss/                    # XML builder/parser ABRASF
│   │   └── tasks/                   # Celery
│   ├── storage/{certificados,xmls}  # Ignorados pelo git
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx + main.jsx
│   │   ├── api.js
│   │   ├── components/              # Layout, UI primitives
│   │   └── views/                   # Dashboard, Clientes, Consultas, Nfse
│   ├── package.json · vite.config.js
│   ├── nginx.conf · Dockerfile
├── docker-compose.yml
├── CUBO_CAPTURA_SPEC.md
└── README.md
```

## Testes manuais sugeridos

1. `POST /api/clientes` com CNPJ de teste.
2. Upload de certificado A1 válido via `POST /api/clientes/{id}/certificado`.
3. `POST /api/consultas` com `tipo=periodo_emissao` e período do mês corrente.
4. Verificar XMLs em `backend/storage/xmls/{cnpj}/{YYYY-MM}/`.
5. `GET /api/nfse/export` retorna ZIP com todos os XMLs filtrados.

## Roadmap

- **Fase 1 MVP** (atual): captura síncrona, dashboard, download ZIP.
- **Fase 2**: agendamentos Celery, alertas de certificado vencendo.
- **Fase 3**: integração com Nibo (envio automático).
- **Fase 4**: suporte multi-município (outros GISS).

## Licença

Proprietária — Cubo Saúde.
