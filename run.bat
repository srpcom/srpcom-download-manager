@echo off
title SRPCOM Download Manager
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else if exist "python.exe" (
    python.exe main.py
) else (
    python main.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Aplikasi tertutup dengan kode error %ERRORLEVEL%.
    pause
)
