#!/bin/bash
# Test script for gmcp

set -e

echo "=== Testing gmcp ==="
echo ""

# Check if FastAPI server is running
if ! curl -s http://localhost:5000/docs > /dev/null; then
    echo "❌ FastAPI server not running on http://localhost:5000"
    echo ""
    echo "Start the sample server first:"
    echo "  cd examples"
    echo "  pip install fastapi uvicorn"
    echo "  python sample_api.py"
    exit 1
fi

echo "✅ FastAPI server is running"
echo ""

# Test gmcp
echo "Testing gmcp tool discovery..."
echo ""
gmcp --list-tools http://localhost:5000
