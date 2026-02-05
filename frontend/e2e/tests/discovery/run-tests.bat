@echo off
REM Discovery Page E2E Test Runner for Windows
REM
REM Usage:
REM   run-tests.bat              - Run all tests
REM   run-tests.bat --ui         - Run with UI mode
REM   run-tests.bat --debug      - Run in debug mode
REM   run-tests.bat --headed     - Run in headed mode
REM   run-tests.bat --report     - Generate and show report

setlocal

cd /d "%~dp0..\..\..\"

echo ================================================================
echo 🐯 Tiger ID - Discovery Page E2E Tests
echo ================================================================
echo.

REM Check if npx is available
where npx >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: npx not found. Please install Node.js and npm.
    exit /b 1
)

REM Parse arguments
set MODE=default
if "%1"=="--ui" (
    set MODE=ui
    echo 🎯 Running in UI mode...
) else if "%1"=="--debug" (
    set MODE=debug
    echo 🐛 Running in debug mode...
) else if "%1"=="--headed" (
    set MODE=headed
    echo 👁️  Running in headed mode...
) else if "%1"=="--report" (
    set MODE=report
    echo 📊 Generating test report...
) else (
    echo 🚀 Running all Discovery tests...
)

echo.

REM Run tests based on mode
if "%MODE%"=="ui" (
    npx playwright test e2e/tests/discovery/ --ui
) else if "%MODE%"=="debug" (
    npx playwright test e2e/tests/discovery/ --debug
) else if "%MODE%"=="headed" (
    npx playwright test e2e/tests/discovery/ --headed
) else if "%MODE%"=="report" (
    npx playwright test e2e/tests/discovery/
    npx playwright show-report
) else (
    npx playwright test e2e/tests/discovery/
)

set EXIT_CODE=%errorlevel%

echo.
echo ================================================================

if %EXIT_CODE%==0 (
    echo ✅ All Discovery tests passed!
) else (
    echo ❌ Some tests failed. Check the output above.
    echo.
    echo 💡 Tip: Run with --debug flag to investigate failures
)

echo ================================================================

exit /b %EXIT_CODE%
