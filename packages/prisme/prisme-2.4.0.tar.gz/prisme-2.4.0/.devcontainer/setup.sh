#!/bin/bash
set -e

echo "Setting up workspace: ${WORKSPACE_NAME}"

# Set up persist volume symlinks
mkdir -p /persist/venv
ln -sfn /persist/venv /workspace/.venv

# Install prisme from local dev source if mounted, otherwise use PyPI version
if [ -f "/prism/pyproject.toml" ]; then
    echo "Installing prisme from local dev source..."
    pip install -e /prism --quiet
    # Ensure prisme is on PATH for exec and shell sessions
    if ! grep -q '/.local/bin' "$HOME/.bashrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    export PATH="$HOME/.local/bin:$PATH"
fi

# Backend setup
if [ -f "pyproject.toml" ]; then
    echo "Installing Python dependencies..."
    uv sync
fi



echo ""
echo "Workspace ready!"
echo "  URL: http://${WORKSPACE_NAME}.localhost"
echo ""
