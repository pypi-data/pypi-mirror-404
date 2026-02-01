#!/bin/bash
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Client root is one level up from bin
CLIENT_ROOT="$(dirname "$SCRIPT_DIR")"
# Project root
PROJECT_ROOT="$(dirname "$(dirname "$CLIENT_ROOT")")"

PROTO_SRC="$PROJECT_ROOT/sec-gemini-infra-common/sec_gemini_infra_common/byot_api.proto"
# Destination in src/sec_gemini_byot
PROTO_DEST_DIR="$CLIENT_ROOT/src/sec_gemini_byot"
PROTO_DEST="$PROTO_DEST_DIR/byot_api.proto"

if [ ! -f "$PROTO_SRC" ]; then
    echo "Error: Proto source not found at $PROTO_SRC"
    exit 1
fi

echo "Copying byot_api.proto from $PROTO_SRC to $PROTO_DEST"
cp "$PROTO_SRC" "$PROTO_DEST"

# Build proto
cd "$CLIENT_ROOT"

echo "Building proto..."
# Using -I src ensures that the generated code imports use the package structure relative to src
uv run python -m grpc_tools.protoc \
    -Isrc \
    --python_out=src \
    --grpc_python_out=src \
    --pyi_out=src \
    src/sec_gemini_byot/byot_api.proto

echo "Done."
