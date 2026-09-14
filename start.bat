@echo off
cd /d "%~dp0"
docker compose up -d
echo.
echo App starting... give it a few seconds, then open:
echo http://localhost:8000
pause