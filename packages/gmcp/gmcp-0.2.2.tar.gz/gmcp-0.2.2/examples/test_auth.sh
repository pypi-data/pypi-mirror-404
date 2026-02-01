#!/bin/bash
# Test script for gmcp with authentication

set -e

echo "=== Testing gmcp with Authentication ==="
echo ""

# Check if secure API is running
if ! curl -s http://localhost:5001/docs > /dev/null; then
    echo "❌ Secure API not running on http://localhost:5001"
    echo ""
    echo "Start the secure API first:"
    echo "  cd examples"
    echo "  pip install fastapi uvicorn"
    echo "  python secure_api.py"
    exit 1
fi

echo "✅ Secure API is running"
echo ""

# Test without auth (should fail)
echo "📋 Test 1: Without authentication (should fail)"
if gmcp --list-tools http://localhost:5001 2>&1 | grep -q "403"; then
    echo "✅ Correctly rejected without API key"
else
    echo "⚠️  Expected 403 error"
fi
echo ""

# Test with correct auth
echo "📋 Test 2: With correct API key"
gmcp --list-tools \
     --auth-type apikey \
     --auth-token "test-key-12345" \
     --auth-header "X-API-Key" \
     http://localhost:5001

echo ""
echo "✅ All tests passed!"
