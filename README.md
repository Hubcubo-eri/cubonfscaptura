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

## Quickstart (produção com Docker + Caddy TLS)

```bash
# 1. Configurar variáveis de ambiente
cp backend/.env.example backend/.env

# 2. Gerar segredos fortes (IMPORTANTE — nunca usar os defaults em produção):
python -c "import secrets; print('MASTER_KEY=' + secrets.token_urlsafe(48))"
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(48))"
# Copie as duas linhas para backend/.env, substituindo os placeholders.

# 3. Definir admin inicial (opcional, mas recomendado):
#    ADMIN_EMAIL=voce@cubosaude.com.br
#    ADMIN_PASSWORD=<senha forte que você vai trocar no primeiro login>
#    ADMIN_NOME=Seu Nome

# 4. Configurar DNS apontando seu domínio para o host e editar Caddyfile:
#    troque captura.cubosaude.com.br pelo domínio real.

# 5. Exportar a senha do Postgres:
export DB_PASSWORD="senha-forte-para-o-banco"

# 6. Subir stack de produção (com Caddy + TLS automático):
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 7. Aplicar migrations:
docker compose exec backend alembic upgrade head
```

A stack expõe apenas as portas 80/443 (Caddy). Backend, frontend, redis e
Postgres ficam na rede interna do Docker.

### Para dev / homologação sem TLS

```bash
docker compose up -d --build          # expõe backend:8000 e frontend:3000
docker compose exec backend alembic upgrade head
```

- Frontend: http://localhost:3000
- Backend / Swagger: http://localhost:8000/docs

## Segredos em produção

| Variável        | Como gerar                                                   |
|-----------------|--------------------------------------------------------------|
| `MASTER_KEY`    | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_SECRET`    | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DB_PASSWORD`   | `openssl rand -base64 32` (ou um gerenciador de senhas)      |

- **Nunca** commite o `backend/.env` real.
- A `MASTER_KEY` cifra as senhas dos certificados A1; se perder, **todas as
  senhas de cert ficam ilegíveis** (é preciso reenviá-las).
- Guarde `MASTER_KEY` e `JWT_SECRET` em um gerenciador de segredos
  (1Password, Bitwarden, AWS Secrets Manager, etc.) com cópia segura
  off-site.

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

## Backup e restore

Scripts em `scripts/backup.sh` e `scripts/restore.sh`. O backup gera dois
arquivos em `./backups/`:

- `db_<timestamp>.sql.gz` — dump lógico do PostgreSQL (`pg_dump`).
- `storage_<timestamp>.tar.gz` — certificados `.pfx` e XMLs capturados.

### Rodar manualmente

```bash
./scripts/backup.sh
```

### Agendar no crontab do host

```cron
# Diário às 02:00 UTC, mantém 30 dias:
0 2 * * * cd /opt/cubo-captura && ./scripts/backup.sh >> /var/log/cubo-backup.log 2>&1
```

Variáveis aceitas: `BACKUP_DIR`, `RETAIN_DAYS`, `DB_SERVICE`, `DB_NAME`,
`DB_USER`, `STORAGE_DIR`, `COMPOSE_FILE`. Para enviar off-site (S3), descomente
as linhas no fim do script.

### Restaurar

```bash
docker compose stop backend worker beat
./scripts/restore.sh 20260418T020000Z
docker compose start backend worker beat
```

**⚠️** o `.env` com `MASTER_KEY` deve ser guardado separadamente do backup.
Sem ela, as senhas de certificado dentro do dump ficam ilegíveis.

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

- **Fase 1 MVP** ✅: captura síncrona, dashboard, download ZIP.
- **Fase 2** ✅: agendamentos Celery, alertas persistidos (cert vencendo).
- **Fase 3**: suporte multi-município (outros GISS).

## Licença

Proprietária — Cubo Saúde.
