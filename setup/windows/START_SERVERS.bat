@echo off
cd /d "%~dp0..\.."

echo ====================================
echo Tiger ID - Starting Servers
echo ====================================
echo.

REM Start Backend API (using venv Python)
start "Tiger ID - Backend API" cmd /k "cd /d %~dp0..\.. && .venv\Scripts\python.exe -m uvicorn backend.api.app:app --reload --port 8000"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start Frontend Dev Server
start "Tiger ID - Frontend" cmd /k "cd /d %~dp0..\..\frontend && npm run dev"

echo.
echo Servers starting in new windows...
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Login: admin / admin
echo.
pause

