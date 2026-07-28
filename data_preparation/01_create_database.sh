#!/usr/bin/env bash
set -euo pipefail

# ============================================
# 01_create_database.sh
# Maakt de lokale PostGIS database + gebruiker aan voor het OV Game project.
# Leest instellingen uit khorstmanshoff_user_config.ini (zelfde map als dit script).
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/khorstmanshoff_user_config.ini"   # of jouw eigen ini-bestand

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "FOUT: configuratiebestand niet gevonden: $CONFIG_FILE"
    exit 1
fi

set -o allexport
source "$CONFIG_FILE"
set +o allexport

echo "============================================"
echo "Database aanmaken: $DB_NAME op $DB_HOST:$DB_PORT"
echo "============================================"

export PGPASSWORD="$PG_SUPERUSER_PASSWORD"

DB_EXISTS=$("$PGBIN/psql" -h "$DB_HOST" -p "$DB_PORT" -U "$PG_SUPERUSER" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")

if [[ "$DB_EXISTS" == "1" ]]; then
    echo "Database $DB_NAME bestaat al, wordt overgeslagen."
else
    "$PGBIN/createdb" -h "$DB_HOST" -p "$DB_PORT" -U "$PG_SUPERUSER" "$DB_NAME"
    echo "Database $DB_NAME aangemaakt."
fi

"$PGBIN/psql" -h "$DB_HOST" -p "$DB_PORT" -U "$PG_SUPERUSER" -d "$DB_NAME" \
    -c "CREATE EXTENSION IF NOT EXISTS postgis;"

USER_EXISTS=$("$PGBIN/psql" -h "$DB_HOST" -p "$DB_PORT" -U "$PG_SUPERUSER" -d postgres -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'")

if [[ "$USER_EXISTS" == "1" ]]; then
    echo "Gebruiker $DB_USER bestaat al, wordt overgeslagen."
else
    "$PGBIN/psql" -h "$DB_HOST" -p "$DB_PORT" -U "$PG_SUPERUSER" -d postgres \
        -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    echo "Gebruiker $DB_USER aangemaakt."
fi

"$PGBIN/psql" -h "$DB_HOST" -p "$DB_PORT" -U "$PG_SUPERUSER" -d "$DB_NAME" \
    -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
"$PGBIN/psql" -h "$DB_HOST" -p "$DB_PORT" -U "$PG_SUPERUSER" -d "$DB_NAME" \
    -c "GRANT ALL ON SCHEMA public TO $DB_USER;"

echo "============================================"
echo "Klaar. Database $DB_NAME staat klaar met PostGIS en gebruiker $DB_USER."
echo "============================================"
