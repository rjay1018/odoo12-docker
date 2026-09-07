#!/bin/bash
set -e

echo "==> Python version: $(python3 --version)"
echo "==> Auto-fixing f-strings in addons (Python 3.5 compatibility layer)..."
find /mnt/extra-addons -name "*.py" -exec f2format {} + 2>/dev/null || true
echo "==> F-string fix complete."

echo "==> Checking for Jasper Reports compile script..."
COMPILE_SCRIPT=$(find /mnt/extra-addons -name "compile.sh" -path "*/jasper_reports/java/compile.sh" -print -quit)
if [ -n "$COMPILE_SCRIPT" ]; then
    echo "==> Compiling Jasper Reports Java dependencies..."
    COMPILE_DIR=$(dirname "$COMPILE_SCRIPT")
    cd "$COMPILE_DIR"
    bash compile.sh
    cd -
fi

echo "==> Starting Odoo..."

# Start Odoo with the config file
exec /usr/bin/odoo --config=/etc/odoo/odoo.conf
