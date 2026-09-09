#!/bin/bash
# Odoo 12 Database & Filestore Restore Script

echo "======================================"
echo "    Odoo 12 Interactive Restore       "
echo "======================================"
echo ""

read -p "Enter the database name to restore to (e.g. yyy): " DB_NAME
if [ -z "$DB_NAME" ]; then
    echo "❌ Error: Database name cannot be empty."
    exit 1
fi

read -p "Enter the path to the SQL backup file (e.g. ./yyy.sql): " SQL_FILE
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: SQL file '$SQL_FILE' not found!"
    exit 1
fi

read -p "Enter the path to the filestore backup folder (e.g. ./filestore/yyy): " FILESTORE_PATH
FILESTORE_PATH=$(realpath "$FILESTORE_PATH")
if [ ! -d "$FILESTORE_PATH" ]; then
    echo "❌ Error: Filestore directory '$FILESTORE_PATH' not found!"
    exit 1
fi

echo ""
echo "You are about to restore:"
echo "Database Name: $DB_NAME"
echo "SQL File:      $SQL_FILE"
echo "Filestore:     $FILESTORE_PATH"
echo "Target folder: /var/lib/odoo/filestore/$DB_NAME inside the container"
echo ""
read -p "Are you sure you want to proceed? This will overwrite the existing database. (y/n): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""

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
