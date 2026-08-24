#!/bin/bash
set -e

echo "==> Python version: $(python3 --version)"
echo "==> Auto-fixing f-strings in addons (Python 3.5 compatibility layer)..."
find /mnt/extra-addons -name "*.py" -exec f2format {} + 2>/dev/null || true
echo "==> F-string fix complete. Starting Odoo..."

# Start Odoo with the config file
exec /usr/bin/odoo --config=/etc/odoo/odoo.conf
