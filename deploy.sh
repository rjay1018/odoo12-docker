#!/bin/bash
# Odoo 12 Docker Deployment Script
# Fully self-healing and path-independent

set -e

# Ensure we are running from the directory where the script is located
cd "$(dirname "$0")"

echo "==> Pulling latest changes from GitHub..."
git pull

echo "==> Ensuring Database Container and Networks are running..."
cd odoo
docker-compose up -d db
cd ..

# Build the custom docker image if it doesn't exist
if ! docker image inspect odoo12-py37 >/dev/null 2>&1; then
    echo "==> Custom Docker image 'odoo12-py37' not found. Building it now..."
    cd odoo
    docker-compose build
    cd ..
fi

echo "==> Fixing addon file permissions (UID 101 = odoo user inside container)..."
sudo chown -R 101:101 $(pwd)/odoo/addons/ 2>/dev/null || echo "⚠️ Warning: Could not chown addons. You may need to run this script with sudo."

echo "==> Restarting Odoo container..."
# Remove the old container if it exists
docker rm -f odoo-web 2>/dev/null || true

# Run the new container
docker run -d \
  --name odoo-web \
  --network odoo_internal-db \
  --network nginx-proxy-network \
  -p 8069:8069 \
  -e HOST=db \
  -e USER=odoo \
  -e PASSWORD=odoo \
  -v odoo_odoo-web-data:/var/lib/odoo \
  -v $(pwd)/odoo/config:/etc/odoo \
  -v $(pwd)/odoo/addons:/opt/odoo12/custom \
  --restart always \
  odoo12-py37

echo "==> Waiting for Odoo to start..."
sleep 5

echo "==> Last 20 lines of Odoo log:"
docker logs --tail 20 odoo-web

echo ""
echo "✅ Done! Open your browser to access Odoo."
