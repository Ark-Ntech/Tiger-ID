@echo off
cd /d "%~dp0..\.."

echo ====================================
echo Tiger ID - SQLite Setup Verification
echo ====================================
echo.

REM Set demo mode environment variable
set USE_SQLITE_DEMO=true
set DATABASE_URL=sqlite:///data/demo.db
set ENABLE_AUDIT_LOGGING=false

REM Run verification script
.venv\Scripts\python.exe setup\scripts\verify_sqlite_setup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ SQLite setup verified successfully!
    echo.
    echo You can now run:
    echo   setup\windows\START_DEMO.bat
    echo.
) else (
    echo.
    echo ❌ SQLite setup verification failed!
    echo Please check the errors above.
    echo.
)

pause

