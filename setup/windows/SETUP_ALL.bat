@echo off
cd /d "%~dp0..\.."

echo ====================================
echo Tiger ID - Complete Setup
echo ====================================
echo.
echo This will:
echo  - Install Python dependencies
echo  - Install Node.js dependencies
echo  - Setup database
echo  - Create test user
echo.
pause

.venv\Scripts\python.exe setup\scripts\setup_all.py

echo.
pause

