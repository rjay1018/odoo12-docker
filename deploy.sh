#!/bin/bash
# Odoo 12 Docker Deployment Script
# Run this after adding new modules or updating config on the server

set -e

echo "==> Pulling latest changes from GitHub..."
cd ~/odoo12-docker/odoo
git pull

echo "==> Fixing addon file permissions (UID 101 = odoo user inside container)..."
sudo chown -R 101:101 ~/odoo12-docker/odoo/addons/

echo "==> Restarting Odoo container..."
docker-compose up -d

echo "==> Installing required Python packages inside container..."
docker exec -u root odoo-web pip3 install -q https://github.com/aeroo/aeroolib/archive/refs/heads/master.zip openpyxl num2words
docker-compose restart web

echo "==> Waiting for Odoo to start..."
sleep 5

echo "==> Last 20 lines of Odoo log:"
docker logs --tail 20 odoo-web

echo ""
echo "✅ Done! Open http://$(curl -s ifconfig.me):8069 in your browser."
