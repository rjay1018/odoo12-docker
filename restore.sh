#!/bin/bash
# Odoo 12 Database & Filestore Restore Script

echo "======================================"
echo "    Odoo 12 Interactive Restore       "
echo "======================================"
echo ""

# 1. Ask for the base path
read -p "1. Enter the base path containing your backups (e.g. ~/yyy_0909): " BASE_PATH
# Expand tilde (~) to the user's home directory so ~/ works properly
BASE_PATH="${BASE_PATH/#\~/$HOME}"
BASE_PATH=$(realpath "$BASE_PATH")
if [ ! -d "$BASE_PATH" ]; then
    echo "❌ Error: Directory '$BASE_PATH' not found!"
    exit 1
fi

# 2. Ask for the filestore folder
# Try to auto-detect a directory inside the base path
AUTO_FS=$(find "$BASE_PATH" -maxdepth 1 -mindepth 1 -type d | head -n 1)
AUTO_FS=$(basename "$AUTO_FS" 2>/dev/null)

FS_PROMPT="2. Enter the filestore folder name"
[ -n "$AUTO_FS" ] && FS_PROMPT+=" [default: $AUTO_FS]"
read -p "$FS_PROMPT (leave blank to skip): " FS_DIRNAME
FS_DIRNAME="${FS_DIRNAME:-$AUTO_FS}"

if [ -n "$FS_DIRNAME" ]; then
    FILESTORE_PATH="$BASE_PATH/$FS_DIRNAME"
    if [ ! -d "$FILESTORE_PATH" ]; then
        echo "❌ Error: Filestore directory '$FILESTORE_PATH' not found!"
        exit 1
    fi
else
    FILESTORE_PATH=""
fi

# 3. Ask for the SQL file
# Try to auto-detect a .sql file
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

# 4. Ask for the new database name
DEFAULT_DB="${FS_DIRNAME:-${SQL_FILENAME%.sql}}"
if [ "$DEFAULT_DB" == "filestore" ]; then
    DEFAULT_DB="${SQL_FILENAME%.sql}"
fi

read -p "4. Enter the new database name [default: $DEFAULT_DB]: " DB_NAME
DB_NAME="${DB_NAME:-$DEFAULT_DB}"

if [ -z "$DB_NAME" ]; then
    echo "❌ Error: Database name cannot be empty."
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
cd "$(dirname "$0")"
docker rm -f odoo-web 2>/dev/null || true

echo "==> 🗑️ Dropping existing database '$DB_NAME'..."
docker exec -i odoo-db dropdb -U odoo -w --if-exists "$DB_NAME"

echo "==> 🆕 Creating fresh database '$DB_NAME'..."
docker exec -i odoo-db createdb -U odoo -w "$DB_NAME"

echo "==> ⏳ Restoring SQL dump into '$DB_NAME' (this may take a few minutes)..."
cat "$SQL_FILE" | docker exec -i odoo-db psql -U odoo -d "$DB_NAME" -q

if [ -n "$FILESTORE_PATH" ]; then
    echo "==> 📂 Restoring filestore into Docker volume..."
    # We use a temporary busybox container to safely copy files directly into the named volume
    docker run --rm -v "$FILESTORE_PATH":/source -v odoo_odoo-web-data:/dest busybox sh -c "\
        mkdir -p /dest/filestore/$DB_NAME && \
        echo 'Copying files...' && \
        cp -a /source/. /dest/filestore/$DB_NAME/ && \
        echo 'Fixing permissions for odoo user...' && \
        chown -R 101:101 /dest/filestore/$DB_NAME"
else
    echo "==> ⚠️ Skipping filestore restore (no path provided)."
fi

echo "==> 🚀 Starting Odoo back up via deploy.sh..."
./deploy.sh

echo ""
echo "✅ Restore complete! Your database and filestore are ready."
