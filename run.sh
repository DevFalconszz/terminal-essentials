#!/usr/bin/env bash
# run.sh – Inicia o Terminal-Essentials Desktop no ambiente virtual
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [ ! -f "$VENV/bin/python3" ]; then
    echo "⚙  Criando ambiente virtual..."
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet textual
    echo "✅ Dependências instaladas."
fi

exec "$VENV/bin/python3" "$SCRIPT_DIR/aquila_desktop_tui.py" "$@"
