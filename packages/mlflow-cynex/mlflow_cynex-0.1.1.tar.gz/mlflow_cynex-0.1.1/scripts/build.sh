#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEGRATION_DIR="$(dirname "$SCRIPT_DIR")"
CYNEX_DIR="$(dirname "$INTEGRATION_DIR")"

echo "Building Cynex frontend..."
cd "$CYNEX_DIR"
npm ci
VITE_BASE_PATH='/static-files/cynex/' npm run build

echo "Copying dist to package..."
STATIC_DIR="$INTEGRATION_DIR/src/mlflow_cynex/static/cynex"
rm -rf "$STATIC_DIR"
mkdir -p "$STATIC_DIR"
cp -r "$CYNEX_DIR/dist/"* "$STATIC_DIR/"

echo "Removing sample data..."
rm -rf "$STATIC_DIR/data"

echo "Building Python wheel..."
cd "$INTEGRATION_DIR"
rm -rf dist build *.egg-info
python -m build

echo ""
echo "Build complete! Wheel available at:"
ls -la "$INTEGRATION_DIR/dist/"*.whl
