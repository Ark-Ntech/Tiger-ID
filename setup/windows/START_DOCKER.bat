@echo off
cd /d "%~dp0..\.."

echo ====================================
echo Tiger ID - Docker Quickstart
echo ====================================
echo.
echo Starting ALL services with Docker:
echo  - PostgreSQL + Redis
echo  - Backend API (auto-setup)
echo  - Frontend Dev Server
echo.

docker compose -f docker-compose.quickstart.yml down 2>nul
docker compose -f docker-compose.quickstart.yml up -d

echo.
echo Waiting for services (30 seconds)...
timeout /t 30 /nobreak

echo.
echo ====================================
echo Tiger ID Ready! 
echo ====================================
echo.
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Login: admin / admin
echo.
echo View logs: docker compose -f docker-compose.quickstart.yml logs -f
echo Stop all:  docker compose -f docker-compose.quickstart.yml down
echo.
pause

