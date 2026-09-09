#!/bin/bash
set -e

echo "==> Python version: $(python3 --version)"
echo "==> Auto-fixing f-strings in addons (Python 3.5 compatibility layer)..."
find /opt/odoo12/custom/addons -name "*.py" -exec f2format {} + 2>/dev/null || true
echo "==> F-string fix complete. Patching aeroolib for Python 3 compatibility..."
sed -i 's/import urllib/import urllib.parse/' /usr/local/lib/python3.8/dist-packages/aeroolib/plugins/opendocument.py 2>/dev/null || true
sed -i 's/urllib.unquote/urllib.parse.unquote/g' /usr/local/lib/python3.8/dist-packages/aeroolib/plugins/opendocument.py 2>/dev/null || true
echo "==> Starting Odoo..."

# Start Odoo with the config file
exec /usr/bin/odoo --config=/etc/odoo/odoo.conf
