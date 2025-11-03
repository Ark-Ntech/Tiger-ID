@echo off
cd /d "%~dp0..\.."

echo ====================================
echo Tiger ID - Database Setup
echo ====================================
echo.
echo This will:
echo  - Run database migrations
echo  - Create test user (admin/admin)
echo.
echo Make sure PostgreSQL is running!
echo.
pause

.venv\Scripts\python.exe setup\scripts\setup_database.py

echo.
pause

