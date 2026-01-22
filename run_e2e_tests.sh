#!/usr/bin/env bash

# KRAFTD E2E TEST RUNNER
# Quick start script for running end-to-end workflow tests

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    KRAFTD E2E TEST RUNNER                          ║"
echo "║           End-to-End Workflow and Quota Enforcement Tests          ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if token provided
if [ -z "$1" ]; then
    echo "❌ ERROR: JWT token required"
    echo ""
    echo "📋 USAGE:"
    echo "   ./run_e2e_tests.sh <JWT_TOKEN>"
    echo ""
    echo "📌 EXAMPLE:"
    echo "   ./run_e2e_tests.sh 'eyJhbGciOiJIUzI1NiIs...'"
    echo ""
    echo "📚 For more information, see: KRAFTD_E2E_TESTING_GUIDE.md"
    echo ""
    exit 1
fi

TOKEN="$1"

# Check if server is running
echo "🔍 Checking server health..."
if ! curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "❌ ERROR: Server not running on http://localhost:8000"
    echo ""
    echo "💡 Start the server with:"
    echo "   cd backend && python main.py"
    echo ""
    exit 1
fi
echo "✅ Server is running"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python not found"
    echo "💡 Install Python 3.8+ and try again"
    exit 1
fi

# Determine Python command
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if requests library is available
echo "📦 Checking dependencies..."
if ! $PYTHON_CMD -c "import requests" 2>/dev/null; then
    echo "⚠️  Missing requests library"
    echo "💡 Install with: pip install requests"
    exit 1
fi
echo "✅ Dependencies OK"
echo ""

# Run the test suite
echo "🚀 Running E2E test suite..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

$PYTHON_CMD KRAFTD_E2E_TEST.py "$TOKEN"

exit_code=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $exit_code -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "📊 Next Steps:"
    echo "   1. Review test output above"
    echo "   2. Verify Cosmos DB documents"
    echo "   3. Check quota counters"
    echo "   4. Deploy to Azure if ready"
    echo ""
else
    echo "❌ Some tests failed"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Check server logs: tail -f backend/app.log"
    echo "   2. Verify Cosmos DB connection"
    echo "   3. Review KRAFTD_E2E_TESTING_GUIDE.md for details"
    echo ""
fi

exit $exit_code
