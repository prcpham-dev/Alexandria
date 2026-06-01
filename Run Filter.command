#!/bin/bash
# Alexandria – Mac launcher
# Double-click this file to run Alexandria.
# First time: automatically installs everything needed.

cd "$(dirname "$0")"

# First-time setup
if [ ! -f "venv/bin/python" ]; then
    echo "First-time setup – this only happens once..."
    python3 -m venv venv
    venv/bin/pip install python-docx --quiet
    echo "Setup complete!"
fi

venv/bin/python app.py
