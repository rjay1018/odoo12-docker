#!/bin/bash
# Odoo 12 Database & Filestore Restore Script

if [ "$#" -ne 3 ]; then
    echo "Usage: ./restore.sh <database_name> <path_to_sql_file> <path_to_filestore_folder>"
    echo "Example: ./restore.sh yyy ./yyy_backup.sql ./filestore/yyy"
    exit 1
fi

DB_NAME=$1
SQL_FILE=$2
FILESTORE_PATH=$(realpath "$3")

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: SQL file '$SQL_FILE' not found!"
    exit 1
fi

if [ ! -d "$FILESTORE_PATH" ]; then
    echo "❌ Error: Filestore directory '$FILESTORE_PATH' not found!"
    exit 1
fi

echo "==> 🛑 Stopping Odoo web container to release database locks..."
cd ~/odoo12-docker
docker rm -f odoo-web 2>/dev/null || true

echo "==> 🗑️ Dropping existing database '$DB_NAME'..."
docker exec -i odoo-db dropdb -U odoo -w --if-exists "$DB_NAME"

echo "==> 🆕 Creating fresh database '$DB_NAME'..."
docker exec -i odoo-db createdb -U odoo -w "$DB_NAME"

echo "==> ⏳ Restoring SQL dump into '$DB_NAME' (this may take a few minutes)..."
cat "$SQL_FILE" | docker exec -i odoo-db psql -U odoo -d "$DB_NAME" -q

echo "==> 📂 Restoring filestore into Docker volume..."
# We use a temporary busybox container to safely copy files directly into the named volume
docker run --rm -v "$FILESTORE_PATH":/source -v odoo_odoo-web-data:/dest busybox sh -c "\
    mkdir -p /dest/filestore/$DB_NAME && \
    echo 'Copying files...' && \
    cp -a /source/. /dest/filestore/$DB_NAME/ && \
    echo 'Fixing permissions for odoo user...' && \
    chown -R 101:101 /dest/filestore/$DB_NAME"

echo "==> 🚀 Starting Odoo back up via deploy.sh..."
./deploy.sh

echo ""
echo "✅ Restore complete! Your database and filestore are ready."
