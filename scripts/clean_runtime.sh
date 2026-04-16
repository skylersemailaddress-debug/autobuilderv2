#!/bin/bash

# AutobuilderV2 Runtime Cleanup
#
# Safely removes all generated runtime artifacts and noise.
# Does NOT remove source, tests, or docs.
# Safe to run repeatedly.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== AutobuilderV2 Runtime Cleanup ==="
echo "Project root: $PROJECT_ROOT"
echo ""
echo "This script will remove:"
echo "  - runs/*.json"
echo "  - memory/*.json"
echo "  - __pycache__ directories"
echo "  - *.pyc files"
echo "  - .pytest_cache directories"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo "Cleaning runtime artifacts..."

# Remove run json files
if [ -d "$PROJECT_ROOT/runs" ]; then
    find "$PROJECT_ROOT/runs" -name "*.json" -type f -delete
    echo "✓ Cleaned runs/*.json"
fi

# Remove memory json files
if [ -d "$PROJECT_ROOT/memory" ]; then
    find "$PROJECT_ROOT/memory" -name "*.json" -type f -delete
    echo "✓ Cleaned memory/*.json"
fi

# Remove __pycache__ directories recursively
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "✓ Cleaned __pycache__"

# Remove .pyc files
find "$PROJECT_ROOT" -type f -name "*.pyc" -delete
echo "✓ Cleaned *.pyc files"

# Remove .pytest_cache directories
find "$PROJECT_ROOT" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo "✓ Cleaned .pytest_cache"

echo ""
echo "=== Cleanup Complete ==="
echo "Runtime artifacts removed. Source, tests, and docs preserved."
echo ""
