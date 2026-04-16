#!/bin/bash

# AutobuilderV2 Release Packaging
#
# Creates a clean, distributable package of AutobuilderV2 source, docs, tests, and config.
# Excludes all runtime-generated artifacts and noise.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VERSION=$(cat "$PROJECT_ROOT/VERSION" 2>/dev/null || echo "unknown")
PACKAGE_NAME="autobuilderv2_${VERSION}_${TIMESTAMP}"
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/$PACKAGE_NAME"

function cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "=== AutobuilderV2 Release Packaging ==="
echo "Version: $VERSION"
echo "Package: $PACKAGE_NAME"
echo ""

# Create package directory structure
mkdir -p "$PACKAGE_DIR"

echo "Copying source and configuration..."

# Core source directories
for dir in cli execution memory state planner orchestrator executor validator debugger \
           control_plane readiness quality policies mutation observability benchmarks; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        cp -r "$PROJECT_ROOT/$dir" "$PACKAGE_DIR/"
    fi
done

# Documentation
for file in README.md VERSION CHANGELOG.md; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        cp "$PROJECT_ROOT/$file" "$PACKAGE_DIR/"
    fi
done

# Documentation directory
if [ -d "$PROJECT_ROOT/docs" ]; then
    cp -r "$PROJECT_ROOT/docs" "$PACKAGE_DIR/"
fi

# Tests
if [ -d "$PROJECT_ROOT/tests" ]; then
    cp -r "$PROJECT_ROOT/tests" "$PACKAGE_DIR/"
fi

# Scripts
if [ -d "$PROJECT_ROOT/scripts" ]; then
    cp -r "$PROJECT_ROOT/scripts" "$PACKAGE_DIR/"
fi

# Configuration files
for file in pyproject.toml .gitignore; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        cp "$PROJECT_ROOT/$file" "$PACKAGE_DIR/"
    fi
done

echo "✓ Copied source, docs, tests, and config"

# Create the zip archive
OUTPUT_DIR="$PROJECT_ROOT/dist"
mkdir -p "$OUTPUT_DIR"
OUTPUT_PATH="$OUTPUT_DIR/${PACKAGE_NAME}.zip"

cd "$TEMP_DIR"
zip -r "$OUTPUT_PATH" "$PACKAGE_NAME" > /dev/null 2>&1

echo ""
echo "=== Packaging Complete ==="
echo "Package created: $OUTPUT_PATH"
echo "Size: $(du -h "$OUTPUT_PATH" | cut -f1)"
echo ""
echo "Contents:"
echo "  ✓ Source code (cli/, execution/, planner/, etc.)"
echo "  ✓ Tests (tests/)"
echo "  ✓ Documentation (docs/, README.md, CHANGELOG.md)"
echo "  ✓ Scripts (scripts/)"
echo "  ✓ Configuration (pyproject.toml, .gitignore)"
echo ""
echo "Excluded:"
echo "  ✗ Runtime artifacts (runs/, memory/ JSON files)"
echo "  ✗ Python cache (__pycache__, *.pyc)"
echo "  ✗ Virtual environment (.venv/)"
echo "  ✗ Test cache (.pytest_cache/)"
echo ""
