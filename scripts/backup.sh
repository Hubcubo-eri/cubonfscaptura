#!/usr/bin/env bash
#
# Backup do CUBO Captura: PostgreSQL (pg_dump), storage de certificados e XMLs.
#
# Uso (via crontab diário às 02:00):
#   0 2 * * * /opt/cubo-captura/scripts/backup.sh >> /var/log/cubo-backup.log 2>&1
#
# Variáveis aceitas (com defaults):
#   BACKUP_DIR    destino local dos arquivos (default: ./backups)
#   RETAIN_DAYS   dias para manter (default: 30)
#   DB_SERVICE    nome do serviço compose do banco (default: db)
#   DB_NAME       nome do banco (default: cubo_captura)
#   DB_USER       user do banco (default: cubo)
#   STORAGE_DIR   diretório do storage local (default: backend/storage)
#   COMPOSE_FILE  arquivo compose para exec (default: docker-compose.yml)
#
# Requer: docker, tar, gzip, date.
#
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETAIN_DAYS="${RETAIN_DAYS:-30}"
DB_SERVICE="${DB_SERVICE:-db}"
DB_NAME="${DB_NAME:-cubo_captura}"
DB_USER="${DB_USER:-cubo}"
STORAGE_DIR="${STORAGE_DIR:-backend/storage}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${BACKUP_DIR}"

log() { echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*"; }

# ----------------------------------------------------------------- Postgres
DB_FILE="${BACKUP_DIR}/db_${TS}.sql.gz"
log "Dump do banco ${DB_NAME} -> ${DB_FILE}"
docker compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
	pg_dump -U "${DB_USER}" -d "${DB_NAME}" --no-owner --no-privileges \
	| gzip -9 > "${DB_FILE}"

# Verifica tamanho mínimo para detectar falhas silenciosas (ex: banco vazio
# costuma ter ~500 bytes comprimido; consideramos saudável >= 200 bytes).
DB_SIZE="$(stat -c %s "${DB_FILE}" 2>/dev/null || stat -f %z "${DB_FILE}")"
if [ "${DB_SIZE}" -lt 200 ]; then
	log "ERRO: dump do banco parece vazio (${DB_SIZE} bytes)"
	exit 1
fi
log "Dump OK: ${DB_SIZE} bytes"

# -------------------------------------------------------- Storage (certs + xmls)
STORAGE_FILE="${BACKUP_DIR}/storage_${TS}.tar.gz"
if [ -d "${STORAGE_DIR}" ]; then
	log "Arquivando ${STORAGE_DIR} -> ${STORAGE_FILE}"
	tar -czf "${STORAGE_FILE}" -C "$(dirname "${STORAGE_DIR}")" "$(basename "${STORAGE_DIR}")"
	log "Storage OK: $(stat -c %s "${STORAGE_FILE}" 2>/dev/null || stat -f %z "${STORAGE_FILE}") bytes"
else
	log "Aviso: ${STORAGE_DIR} não existe — pulando storage"
fi

# ----------------------------------------------------------------- Rotação
log "Removendo backups com mais de ${RETAIN_DAYS} dias"
find "${BACKUP_DIR}" -maxdepth 1 -type f \
	\( -name 'db_*.sql.gz' -o -name 'storage_*.tar.gz' \) \
	-mtime +"${RETAIN_DAYS}" -print -delete || true

log "Backup concluído."

# --------------------------------------------------- Envio off-site (opcional)
# Descomente se usar S3 (requer AWS CLI configurado):
# aws s3 cp "${DB_FILE}"      "s3://${BACKUP_BUCKET}/cubo-captura/${TS}/" --storage-class STANDARD_IA
# aws s3 cp "${STORAGE_FILE}" "s3://${BACKUP_BUCKET}/cubo-captura/${TS}/" --storage-class STANDARD_IA
