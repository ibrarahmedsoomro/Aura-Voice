@echo off
echo ========================================================
echo        AURA VOICE (VOXAGENT) - AUTONOMOUS AI VOICE AGENT
echo ========================================================
echo Starting Backend API (FastAPI) on http://localhost:8000...
start "Aura Voice Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe main.py"

echo Starting Frontend UI on http://localhost:3000...
start "Aura Voice Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers are starting!
echo Open your browser at: http://localhost:3000
echo ========================================================
pause
