@echo off
REM Investigation E2E Test Runner (Windows)
REM Provides convenient commands for running investigation tests

setlocal enabledelayedexpansion

echo === Investigation 2.0 E2E Tests ===
echo.

set TEST_FILE=investigation.spec.ts
set CATEGORY=%1

if "%CATEGORY%"=="" set CATEGORY=all

if "%CATEGORY%"=="all" (
    echo Running all investigation tests...
    npx playwright test %TEST_FILE%
    goto :end
)

if "%CATEGORY%"=="upload" (
    echo Running image upload tests...
    npx playwright test %TEST_FILE% -g "Image Upload"
    goto :end
)

if "%CATEGORY%"=="context" (
    echo Running context form tests...
    npx playwright test %TEST_FILE% -g "Context Form"
    goto :end
)

if "%CATEGORY%"=="launch" (
    echo Running investigation launch tests...
    npx playwright test %TEST_FILE% -g "Investigation Launch"
    goto :end
)

if "%CATEGORY%"=="progress" (
    echo Running progress display tests...
    npx playwright test %TEST_FILE% -g "Progress Display"
    goto :end
)

if "%CATEGORY%"=="models" (
    echo Running model progress grid tests...
    npx playwright test %TEST_FILE% -g "Model Progress Grid"
    goto :end
)

if "%CATEGORY%"=="results" (
    echo Running results display tests...
    npx playwright test %TEST_FILE% -g "Results Display"
    goto :end
)

if "%CATEGORY%"=="matches" (
    echo Running match card interaction tests...
    npx playwright test %TEST_FILE% -g "Match Card Interactions"
    goto :end
)

if "%CATEGORY%"=="filters" (
    echo Running filters and search tests...
    npx playwright test %TEST_FILE% -g "Filters and Search"
    goto :end
)

if "%CATEGORY%"=="report" (
    echo Running report generation tests...
    npx playwright test %TEST_FILE% -g "Report Generation"
    goto :end
)

if "%CATEGORY%"=="methodology" (
    echo Running methodology tracking tests...
    npx playwright test %TEST_FILE% -g "Methodology Tracking"
    goto :end
)

if "%CATEGORY%"=="errors" (
    echo Running error handling tests...
    npx playwright test %TEST_FILE% -g "Error Handling"
    goto :end
)

if "%CATEGORY%"=="detection" (
    echo Running detection results tests...
    npx playwright test %TEST_FILE% -g "Detection Results"
    goto :end
)

if "%CATEGORY%"=="overview" (
    echo Running overview tab tests...
    npx playwright test %TEST_FILE% -g "Overview Tab"
    goto :end
)

if "%CATEGORY%"=="verification" (
    echo Running verification tab tests...
    npx playwright test %TEST_FILE% -g "Verification Tab"
    goto :end
)

if "%CATEGORY%"=="headed" (
    echo Running all tests in headed mode ^(visible browser^)...
    npx playwright test %TEST_FILE% --headed
    goto :end
)

if "%CATEGORY%"=="debug" (
    echo Running all tests in debug mode...
    npx playwright test %TEST_FILE% --debug
    goto :end
)

if "%CATEGORY%"=="ui" (
    echo Opening Playwright UI mode...
    npx playwright test %TEST_FILE% --ui
    goto :end
)

REM Show usage if unknown category
echo Usage: %0 [category]
echo.
echo Categories:
echo   all           - Run all tests ^(default^)
echo   upload        - Image upload tests
echo   context       - Context form tests
echo   launch        - Investigation launch tests
echo   progress      - Progress display tests
echo   models        - Model progress grid tests
echo   results       - Results display tests
echo   matches       - Match card interaction tests
echo   filters       - Filters and search tests
echo   report        - Report generation tests
echo   methodology   - Methodology tracking tests
echo   errors        - Error handling tests
echo   detection     - Detection results tests
echo   overview      - Overview tab tests
echo   verification  - Verification tab tests
echo.
echo Special modes:
echo   headed        - Run with visible browser
echo   debug         - Run in debug mode
echo   ui            - Open Playwright UI
echo.
echo Examples:
echo   %0 upload      # Run only upload tests
echo   %0 headed      # Run all tests with browser visible
echo   %0 ui          # Open interactive UI

:end
echo.
echo === Test run complete ===
endlocal
