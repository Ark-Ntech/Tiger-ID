#!/bin/bash

# Discovery Page E2E Test Runner
#
# Usage:
#   ./run-tests.sh              # Run all tests
#   ./run-tests.sh --ui         # Run with UI mode
#   ./run-tests.sh --debug      # Run in debug mode
#   ./run-tests.sh --headed     # Run in headed mode
#   ./run-tests.sh --report     # Generate and show report

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$FRONTEND_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐯 Tiger ID - Discovery Page E2E Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Playwright is installed
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx not found. Please install Node.js and npm."
    exit 1
fi

# Parse arguments
MODE="default"
if [ "$1" == "--ui" ]; then
    MODE="ui"
    echo "🎯 Running in UI mode..."
elif [ "$1" == "--debug" ]; then
    MODE="debug"
    echo "🐛 Running in debug mode..."
elif [ "$1" == "--headed" ]; then
    MODE="headed"
    echo "👁️  Running in headed mode..."
elif [ "$1" == "--report" ]; then
    MODE="report"
    echo "📊 Generating test report..."
else
    echo "🚀 Running all Discovery tests..."
fi

echo ""

# Run tests based on mode
case $MODE in
    ui)
        npx playwright test e2e/tests/discovery/ --ui
        ;;
    debug)
        npx playwright test e2e/tests/discovery/ --debug
        ;;
    headed)
        npx playwright test e2e/tests/discovery/ --headed
        ;;
    report)
        npx playwright test e2e/tests/discovery/ || true
        npx playwright show-report
        ;;
    default)
        npx playwright test e2e/tests/discovery/
        ;;
esac

EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All Discovery tests passed!"
else
    echo "❌ Some tests failed. Check the output above."
    echo ""
    echo "💡 Tip: Run with --debug flag to investigate failures"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EXIT_CODE
