#!/bin/bash
# Odoo 12 Production Docker Deployment Script
# Fully isolated from staging environment

set -e

# Ensure we are running from the directory where the script is located
cd "$(dirname "$0")"

echo "==> Pulling latest changes from GitHub..."
git pull
git submodule update --init --recursive

echo "==> Ensuring Docker networks and production volumes exist..."
docker network create nginx-proxy-network 2>/dev/null || true
docker volume create odoo_odoo-web-prod-data 2>/dev/null || true

# Determine compose command
COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

echo "==> Ensuring Nginx reverse proxy & SSL companion are running..."
if [ -d "proxy" ]; then
    $COMPOSE_CMD -f proxy/docker-compose.yml up -d
    docker exec nginx-proxy nginx -s reload 2>/dev/null || true
fi

echo "==> Ensuring Host PostgreSQL is running..."
if command -v systemctl >/dev/null 2>&1; then
    if ! systemctl is-active --quiet postgresql; then
        echo "Starting PostgreSQL on host..."
        sudo systemctl start postgresql
    fi
fi

# Build the custom docker image if it doesn't exist
if ! docker image inspect odoo12-py37 >/dev/null 2>&1; then
    echo "==> Custom Docker image 'odoo12-py37' not found. Building it now..."
    docker build -t odoo12-py37 odoo/
fi

echo "==> Fixing addon file permissions (UID 101 = odoo user inside container)..."
sudo chown -R 101:101 $(pwd)/odoo/addons/ 2>/dev/null || echo "⚠️ Warning: Could not chown addons. You may need to run this script with sudo."

echo "==> Restarting Production Odoo container (odoo-web-prod)..."
# Remove the old production container if it exists
docker rm -f odoo-web-prod 2>/dev/null || true

# Run the new production container
docker run -d \
  --name odoo-web-prod \
  --network nginx-proxy-network \
  -p 8079:8069 \
  -e VIRTUAL_HOST=yyy.on-cloud.io \
  -e VIRTUAL_PORT=8069 \
  -e LETSENCRYPT_HOST=yyy.on-cloud.io \
  -e LETSENCRYPT_EMAIL=renato@cml-intl.com \
  -e HOST=False \
  -e USER=yyy \
  -e PASSWORD=2bund2nc3+ \
  -v odoo_odoo-web-prod-data:/var/lib/odoo \
  -v $(pwd)/odoo/config/odoo.prod.conf:/etc/odoo/odoo.conf \
  -v $(pwd)/odoo/addons:/opt/odoo12/custom \
  -v /var/run/postgresql:/var/run/postgresql \
  --restart always \
  odoo12-py37

echo "==> Waiting for Production Odoo to start..."
sleep 5

echo "==> Last 20 lines of Production Odoo log:"
docker logs --tail 20 odoo-web-prod

echo ""
echo "✅ Done! Access Production Odoo at https://yyy.on-cloud.io"
