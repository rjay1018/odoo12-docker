#!/bin/bash
# Odoo 12 Docker Deployment Script
# Fully self-healing and path-independent

set -e

# Ensure we are running from the directory where the script is located
cd "$(dirname "$0")"

echo "==> Pulling latest changes from GitHub..."
git pull

echo "==> Ensuring Docker networks and volumes exist..."
# Note: nginx-proxy-network is external, but we try to create it just in case
docker network create nginx-proxy-network 2>/dev/null || true
docker volume create odoo_odoo-web-data 2>/dev/null || true

# Determine compose command
COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

echo "==> Ensuring Nginx reverse proxy & SSL companion are running..."
if [ -d "proxy" ]; then
    $COMPOSE_CMD -f proxy/docker-compose.yml up -d
fi

echo "==> Ensuring Host PostgreSQL is running..."
if command -v systemctl >/dev/null 2>&1; then
    if ! systemctl is-active --quiet postgresql; then
        echo "Starting PostgreSQL on host..."
        sudo systemctl start postgresql
    fi
fi

# Clean up retired odoo-db container if still running
if docker ps | grep -q odoo-db; then
    echo "==> Stopping retired odoo-db Docker container..."
    docker rm -f odoo-db 2>/dev/null || true
fi

# Build the custom docker image if it doesn't exist
if ! docker image inspect odoo12-py37 >/dev/null 2>&1; then
    echo "==> Custom Docker image 'odoo12-py37' not found. Building it now..."
    docker build -t odoo12-py37 odoo/
fi

echo "==> Fixing addon file permissions (UID 101 = odoo user inside container)..."
sudo chown -R 101:101 $(pwd)/odoo/addons/ 2>/dev/null || echo "⚠️ Warning: Could not chown addons. You may need to run this script with sudo."

echo "==> Restarting Odoo container..."
# Remove the old container if it exists
docker rm -f odoo-web 2>/dev/null || true

# Run the new container
docker run -d \
  --name odoo-web \
  --network nginx-proxy-network \
  -p 8069:8069 \
  -e VIRTUAL_HOST=yyy-staging.on-cloud.io \
  -e VIRTUAL_PORT=8069 \
  -e LETSENCRYPT_HOST=yyy-staging.on-cloud.io \
  -e LETSENCRYPT_EMAIL=renato@cml-intl.com \
  -e HOST=False \
  -e USER=odoo \
  -e PASSWORD=2bund2nc3+ \
  -v odoo_odoo-web-data:/var/lib/odoo \
  -v $(pwd)/odoo/config:/etc/odoo \
  -v $(pwd)/odoo/addons:/opt/odoo12/custom \
  -v /var/run/postgresql:/var/run/postgresql \
  --restart always \
  odoo12-py37

echo "==> Waiting for Odoo to start..."
sleep 5

echo "==> Last 20 lines of Odoo log:"
docker logs --tail 20 odoo-web

echo ""
echo "✅ Done! Access Odoo at https://yyy-staging.on-cloud.io"
