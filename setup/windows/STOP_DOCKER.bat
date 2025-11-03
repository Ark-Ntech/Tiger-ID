@echo off
cd /d "%~dp0..\.."

echo Stopping all Docker services...
docker compose -f docker-compose.quickstart.yml down

echo.
echo All services stopped.
pause

