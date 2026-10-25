#!/bin/bash
# Odoo 12 Production Database & Filestore Restore Script
# Fully isolated from staging environment

set -e

echo "=========================================="
echo "    Odoo 12 Production Database Restore   "
echo "=========================================="
echo ""

# 1. Ask for the base path
read -p "1. Enter the base path containing your backups (e.g. ~/yyy_backup): " BASE_PATH
BASE_PATH="${BASE_PATH/#\~/$HOME}"
BASE_PATH=$(realpath "$BASE_PATH")
if [ ! -d "$BASE_PATH" ]; then
    echo "❌ Error: Directory '$BASE_PATH' not found!"
    exit 1
fi

# 2. Ask for the filestore folder
AUTO_FS=$(find "$BASE_PATH" -maxdepth 1 -mindepth 1 -type d | head -n 1)
AUTO_FS=$(basename "$AUTO_FS" 2>/dev/null)

FS_PROMPT="2. Enter the filestore folder name"
if [ -n "$AUTO_FS" ]; then
    FS_PROMPT+=" [default: $AUTO_FS] (type 'skip' to ignore filestore)"
else
    FS_PROMPT+=" (leave blank to skip)"
fi
read -p "$FS_PROMPT: " FS_DIRNAME
FS_DIRNAME="${FS_DIRNAME:-$AUTO_FS}"

if [ -n "$FS_DIRNAME" ] && [ "$FS_DIRNAME" != "skip" ]; then
    FILESTORE_PATH="$BASE_PATH/$FS_DIRNAME"
    if [ ! -d "$FILESTORE_PATH" ]; then
        echo "❌ Error: Filestore directory '$FILESTORE_PATH' not found!"
        exit 1
    fi
else
    FILESTORE_PATH=""
fi

# 3. Ask for the SQL file
AUTO_SQL=$(ls -1 "$BASE_PATH"/*.sql 2>/dev/null | head -n 1)
AUTO_SQL=$(basename "$AUTO_SQL" 2>/dev/null)

SQL_PROMPT="3. Enter the exact SQL file name"
[ -n "$AUTO_SQL" ] && SQL_PROMPT+=" [default: $AUTO_SQL]"
read -p "$SQL_PROMPT: " SQL_FILENAME
SQL_FILENAME="${SQL_FILENAME:-$AUTO_SQL}"

if [ -z "$SQL_FILENAME" ]; then
    echo "❌ Error: No SQL file specified."
    exit 1
fi

SQL_FILE="$BASE_PATH/$SQL_FILENAME"
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: SQL file '$SQL_FILE' not found!"
    exit 1
fi

# 4. Ask for the database name
DEFAULT_DB="${FS_DIRNAME:-${SQL_FILENAME%.sql}}"
if [ "$DEFAULT_DB" == "filestore" ]; then
    DEFAULT_DB="${SQL_FILENAME%.sql}"
fi

read -p "4. Enter the production database name [default: $DEFAULT_DB]: " DB_NAME
DB_NAME="${DB_NAME:-$DEFAULT_DB}"

echo ""
echo "⚠️  WARNING: You are about to restore to PRODUCTION:"
echo "Database Name: $DB_NAME"
echo "SQL File:      $SQL_FILE"
echo "Filestore:     $FILESTORE_PATH"
echo "Target volume: odoo_odoo-web-prod-data (/var/lib/odoo/filestore/$DB_NAME)"
echo ""
read -p "Are you sure you want to proceed? This will overwrite the production database! (yes/no): " confirm
if [[ $confirm != "yes" && $confirm != "y" ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "==> 🛑 Stopping Production Odoo web container (odoo-web-prod)..."
cd "$(dirname "$0")"
docker rm -f odoo-web-prod 2>/dev/null || true

echo "==> 🗑️ Dropping existing production database '$DB_NAME'..."
sudo -u postgres dropdb --if-exists "$DB_NAME"

echo "==> 🆕 Creating fresh production database '$DB_NAME' owned by 'yyy'..."
sudo -u postgres createdb -O yyy "$DB_NAME"

echo "==> ⏳ Restoring SQL dump into '$DB_NAME'..."
sudo -u postgres psql -d "$DB_NAME" -q < "$SQL_FILE"

echo "==> 🔑 Ensuring schema permissions on public for 'yyy'..."
sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO yyy;" 2>/dev/null || true

echo "==> 🔒 Isolating production database (preventing staging 'odoo' user access)..."
sudo -u postgres psql -c "REVOKE ALL ON DATABASE \"$DB_NAME\" FROM odoo, PUBLIC;" 2>/dev/null || true
sudo -u postgres psql -c "REVOKE CONNECT ON DATABASE \"$DB_NAME\" FROM odoo, PUBLIC;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL ON DATABASE \"$DB_NAME\" TO yyy;" 2>/dev/null || true

if [ -n "$FILESTORE_PATH" ]; then
    echo "==> 📂 Restoring filestore into Production Docker volume (odoo_odoo-web-prod-data)..."
    docker volume create odoo_odoo-web-prod-data 2>/dev/null || true
    docker run --rm -v "$FILESTORE_PATH":/source -v odoo_odoo-web-prod-data:/dest busybox sh -c "\
        mkdir -p /dest/filestore/$DB_NAME && \
        echo 'Copying files...' && \
        cp -a /source/. /dest/filestore/$DB_NAME/ && \
        echo 'Fixing permissions for odoo user...' && \
        chown -R 101:101 /dest/filestore/$DB_NAME"
else
    echo "==> ⚠️ Skipping filestore restore."
fi

echo "==> 🚀 Starting Production Odoo back up via deploy-prod.sh..."
./deploy-prod.sh

echo ""
echo "✅ Production restore complete! Your database and filestore are ready at https://yyy.on-cloud.io"
