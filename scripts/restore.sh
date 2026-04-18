#!/usr/bin/env bash
#
# Restore do CUBO Captura a partir de um snapshot gerado por backup.sh.
#
# Uso:
#   scripts/restore.sh <timestamp>
# Exemplo:
#   scripts/restore.sh 20260418T020000Z
#
# Isso vai:
#  1. Restaurar o dump do PostgreSQL (db_<ts>.sql.gz).
#  2. Extrair o storage (storage_<ts>.tar.gz) sobrescrevendo backend/storage.
#
# ⚠️ IMPORTANTE: PARE a aplicação antes (docker compose stop backend worker beat)
#    para evitar writes concorrentes durante o restore.
set -euo pipefail

if [ $# -lt 1 ]; then
	echo "Uso: $0 <timestamp>" >&2
	exit 1
fi

TS="$1"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_SERVICE="${DB_SERVICE:-db}"
DB_NAME="${DB_NAME:-cubo_captura}"
DB_USER="${DB_USER:-cubo}"
STORAGE_DIR="${STORAGE_DIR:-backend/storage}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

DB_FILE="${BACKUP_DIR}/db_${TS}.sql.gz"
STORAGE_FILE="${BACKUP_DIR}/storage_${TS}.tar.gz"

if [ ! -f "${DB_FILE}" ]; then
	echo "Arquivo não encontrado: ${DB_FILE}" >&2
	exit 1
fi

echo "⚠️  Esta operação vai DROPAR o banco ${DB_NAME} e recriar a partir do backup."
read -rp "Digite 'confirmar' para prosseguir: " answer
[ "${answer}" = "confirmar" ] || { echo "Abortado."; exit 1; }

echo "[1/3] Parando serviços que escrevem no banco/storage…"
docker compose -f "${COMPOSE_FILE}" stop backend worker beat

echo "[2/3] Restaurando banco ${DB_NAME}…"
docker compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
	psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME} WITH (FORCE);"
docker compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
	psql -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
gunzip -c "${DB_FILE}" | docker compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
	psql -U "${DB_USER}" -d "${DB_NAME}"

if [ -f "${STORAGE_FILE}" ]; then
	echo "[3/3] Restaurando storage…"
	rm -rf "${STORAGE_DIR}"
	mkdir -p "$(dirname "${STORAGE_DIR}")"
	tar -xzf "${STORAGE_FILE}" -C "$(dirname "${STORAGE_DIR}")"
fi

echo "Restaurado com sucesso. Para subir de volta:"
echo "  docker compose -f ${COMPOSE_FILE} up -d backend worker beat"
