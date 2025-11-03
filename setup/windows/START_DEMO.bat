@echo off
cd /d "%~dp0..\.."

echo ====================================
echo Tiger ID - DEMO MODE
echo ====================================
echo.
echo Starting in DEMO mode (No PostgreSQL required):
echo  - SQLite database
echo  - Demo data included
echo  - Backend + Frontend
echo.
echo This is perfect for testing the UI!
echo.
pause

REM Set demo mode environment variable
set USE_SQLITE_DEMO=true
set DATABASE_URL=sqlite:///data/demo.db
set ENABLE_AUDIT_LOGGING=false

REM Initialize SQLite database
echo.
echo → Initializing SQLite demo database...
.venv\Scripts\python.exe -m backend.database.sqlite_connection

REM Start Backend API (using venv Python)
start "Tiger ID - Backend (DEMO)" cmd /k "cd /d %~dp0..\.. && set USE_SQLITE_DEMO=true && set DATABASE_URL=sqlite:///data/demo.db && set ENABLE_AUDIT_LOGGING=false && .venv\Scripts\python.exe -m uvicorn backend.api.app:app --reload --port 8000"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start Frontend
start "Tiger ID - Frontend" cmd /k "cd /d %~dp0..\..\frontend && npm run dev"

echo.
echo ====================================
echo Servers Starting (DEMO MODE)
echo ====================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Login credentials:
echo   admin / admin
echo   investigator / demo
echo.
echo Demo data included:
echo   - 2 users
echo   - 150+ facilities (enriched from dataset)
echo   - 700+ tigers (enriched from dataset)
echo   - 3 investigations
echo.
pause

