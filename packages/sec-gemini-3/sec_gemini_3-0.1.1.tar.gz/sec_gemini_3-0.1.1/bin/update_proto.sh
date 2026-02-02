#!/bin/bash
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# SDK root is one level up from bin
SDK_ROOT="$(dirname "$SCRIPT_DIR")"
# Project root is three levels up from SDK root (sdk/python/bin -> sdk/python -> sdk -> root)
# Actually: SDK_ROOT is `.../sdk/python`.
# PROJECT_ROOT is `.../sec-gemini-mark3`.
# sdk/python -> 2 levels up.
PROJECT_ROOT="$(dirname "$(dirname "$SDK_ROOT")")"

PROTO_SRC="$PROJECT_ROOT/sec-gemini-infra-common/sec_gemini_infra_common/api.proto"
PROTO_DEST="$SDK_ROOT/sec_gemini/api.proto"

if [ ! -f "$PROTO_SRC" ]; then
    echo "Error: Proto source not found at $PROTO_SRC"
    exit 1
fi

echo "Copying api.proto from $PROTO_SRC to $PROTO_DEST"
cp "$PROTO_SRC" "$PROTO_DEST"

# Build proto
cd "$SDK_ROOT"

echo "Building proto..."
# We use uv run to ensure we are in the venv and have dependencies
uv run --no-project --with grpcio-tools python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    --pyi_out=. \
    sec_gemini/api.proto

echo "Ensuring __init__.py exists..."
touch "$SDK_ROOT/sec_gemini/__init__.py"

echo "Done."
