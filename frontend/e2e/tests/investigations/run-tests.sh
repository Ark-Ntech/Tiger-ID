#!/bin/bash

# Investigation E2E Test Runner
# Provides convenient commands for running investigation tests

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Investigation 2.0 E2E Tests ===${NC}\n"

# Check if npx is available
if ! command -v npx &> /dev/null; then
    echo -e "${RED}Error: npx is not installed${NC}"
    exit 1
fi

# Function to run tests
run_tests() {
    local args=$1
    echo -e "${YELLOW}Running: npx playwright test investigation.spec.ts $args${NC}\n"
    npx playwright test investigation.spec.ts $args
}

# Parse command line argument
case "${1:-all}" in
    all)
        echo "Running all investigation tests..."
        run_tests ""
        ;;
    upload)
        echo "Running image upload tests..."
        run_tests "-g 'Image Upload'"
        ;;
    context)
        echo "Running context form tests..."
        run_tests "-g 'Context Form'"
        ;;
    launch)
        echo "Running investigation launch tests..."
        run_tests "-g 'Investigation Launch'"
        ;;
    progress)
        echo "Running progress display tests..."
        run_tests "-g 'Progress Display'"
        ;;
    models)
        echo "Running model progress grid tests..."
        run_tests "-g 'Model Progress Grid'"
        ;;
    results)
        echo "Running results display tests..."
        run_tests "-g 'Results Display'"
        ;;
    matches)
        echo "Running match card interaction tests..."
        run_tests "-g 'Match Card Interactions'"
        ;;
    filters)
        echo "Running filters and search tests..."
        run_tests "-g 'Filters and Search'"
        ;;
    report)
        echo "Running report generation tests..."
        run_tests "-g 'Report Generation'"
        ;;
    methodology)
        echo "Running methodology tracking tests..."
        run_tests "-g 'Methodology Tracking'"
        ;;
    errors)
        echo "Running error handling tests..."
        run_tests "-g 'Error Handling'"
        ;;
    detection)
        echo "Running detection results tests..."
        run_tests "-g 'Detection Results'"
        ;;
    overview)
        echo "Running overview tab tests..."
        run_tests "-g 'Overview Tab'"
        ;;
    verification)
        echo "Running verification tab tests..."
        run_tests "-g 'Verification Tab'"
        ;;
    headed)
        echo "Running all tests in headed mode (visible browser)..."
        run_tests "--headed"
        ;;
    debug)
        echo "Running all tests in debug mode..."
        run_tests "--debug"
        ;;
    ui)
        echo "Opening Playwright UI mode..."
        npx playwright test investigation.spec.ts --ui
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 [category]${NC}\n"
        echo "Categories:"
        echo "  all           - Run all tests (default)"
        echo "  upload        - Image upload tests"
        echo "  context       - Context form tests"
        echo "  launch        - Investigation launch tests"
        echo "  progress      - Progress display tests"
        echo "  models        - Model progress grid tests"
        echo "  results       - Results display tests"
        echo "  matches       - Match card interaction tests"
        echo "  filters       - Filters and search tests"
        echo "  report        - Report generation tests"
        echo "  methodology   - Methodology tracking tests"
        echo "  errors        - Error handling tests"
        echo "  detection     - Detection results tests"
        echo "  overview      - Overview tab tests"
        echo "  verification  - Verification tab tests"
        echo ""
        echo "Special modes:"
        echo "  headed        - Run with visible browser"
        echo "  debug         - Run in debug mode"
        echo "  ui            - Open Playwright UI"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  $0 upload      # Run only upload tests"
        echo "  $0 headed      # Run all tests with browser visible"
        echo "  $0 ui          # Open interactive UI"
        exit 1
        ;;
esac

echo -e "\n${GREEN}=== Test run complete ===${NC}"
