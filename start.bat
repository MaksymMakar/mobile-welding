@echo off
title Ironclad Welding - Local Server
cd /d "%~dp0"

echo.
echo ============================================================
echo   Ironclad Welding - Starting Local Server
echo ============================================================
echo.

REM Make sure dependencies are installed
py -m pip install -q -r requirements.txt

REM Open browser after a short delay
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5000"

REM Run Flask
py app.py

echo.
echo Server stopped. Press any key to close.
pause >nul
