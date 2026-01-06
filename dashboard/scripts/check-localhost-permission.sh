#!/bin/bash
# Check if localhost permission exists in package.json
# Run this before starting Raycast dev to catch permission issues early

set -euo pipefail

PACKAGE_JSON="package.json"
REQUIRED_PERMISSION='"localhost": true'

echo "🔍 Checking Raycast localhost permission..."

if grep -q "$REQUIRED_PERMISSION" "$PACKAGE_JSON"; then
    echo "✅ Localhost permission is present in package.json"
    echo "   Extension can connect to http://localhost:8000"
    exit 0
else
    echo "❌ CRITICAL: Localhost permission MISSING from package.json"
    echo ""
    echo "   Without this permission, the extension CANNOT connect to the DSPy backend."
    echo "   You will see: 'DSPy backend not available' errors."
    echo ""
    echo "🔧 FIX: Add this line to package.json after 'license':"
    echo ""
    echo "   {"
    echo "     \"name\": \"prompt-improver-local\","
    echo "     \"license\": \"MIT\","
    echo "     \"localhost\": true,  // ← ADD THIS LINE"
    echo "     \"commands\": [...]"
    echo "   }"
    echo ""
    echo "Then restart Raycast dev server."
    exit 1
fi
