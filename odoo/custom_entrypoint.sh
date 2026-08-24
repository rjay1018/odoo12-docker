#!/bin/bash
set -e

echo "==> Auto-fixing f-strings in addons (Python 3.5 compatibility)..."
find /mnt/extra-addons -name "*.py" -exec f2format {} + 2>/dev/null || true
echo "==> F-string fix complete. Starting Odoo..."

# Hand off to the original official Odoo entrypoint
exec /entrypoint.sh "$@"
