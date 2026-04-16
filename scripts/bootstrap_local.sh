#!/bin/bash

# AutobuilderV2 Local Bootstrap
# 
# Initializes a clean local development environment with all dependencies.
# Safe to run repeatedly.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== AutobuilderV2 Local Bootstrap ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Create virtual environment if it doesn't exist
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$PROJECT_ROOT/.venv"
else
    echo "Virtual environment already exists at $PROJECT_ROOT/.venv"
fi

# Step 2: Activate virtual environment
echo "Activating virtual environment..."
source "$PROJECT_ROOT/.venv/bin/activate"

# Step 3: Upgrade pip and install dependencies
echo "Installing/upgrading pip and setuptools..."
python -m pip install --upgrade pip setuptools wheel 2>&1 | grep -E "(Collecting|Installing|Successfully)" || true

# Step 4: Install project dependencies from pyproject.toml
echo "Installing project dependencies..."
cd "$PROJECT_ROOT"
pip install -e . 2>&1 | grep -E "(Collecting|Installing|Successfully)" || true

echo ""
echo "=== Bootstrap Complete ==="
echo ""
echo "Canonical next commands:"
echo ""
echo "1. Run readiness checks:"
echo "   python cli/autobuilder.py readiness --json"
echo ""
echo "2. Run proof of execution:"
echo "   python cli/autobuilder.py proof --json"
echo ""
echo "3. Run benchmarks:"
echo "   python cli/autobuilder.py benchmark --json"
echo ""
echo "4. Start a mission:"
echo "   python cli/autobuilder.py mission 'Your goal here' --json"
echo ""
