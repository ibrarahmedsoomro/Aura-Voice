@echo off
title Aura Voice Launcher
echo ========================================================
echo        STARTING AURA VOICE (VOXAGENT)
echo   Local AI Engine: Meta MMS VITS (Sindhi/Urdu/Hindi)
echo   Expert Mode: ON
echo ========================================================
echo.

echo [1/2] Starting FastAPI Backend on http://localhost:8001 ...
start "Aura Voice Backend (8001)" cmd /k "cd /d "%~dp0backend" && .\.venv\Scripts\python.exe main.py"

echo Waiting for backend to initialize...
timeout /t 3 >nul

echo [2/2] Starting Frontend Studio on http://localhost:3000 ...
start "Aura Voice Frontend (3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Waiting for frontend to initialize...
timeout /t 3 >nul

echo.
echo ========================================================
echo Opening Aura Voice in your browser...
echo URL: http://localhost:3000
echo ========================================================
start http://localhost:3000
