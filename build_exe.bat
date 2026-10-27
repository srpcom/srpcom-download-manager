@echo off
title SRPCOM Download Manager - Build System
cd /d "%~dp0"

echo =======================================================
echo    SRPCOM DOWNLOAD MANAGER - ALL-IN-ONE BUILD SYSTEM
echo =======================================================
echo.

echo [1/3] Membangun Main App Executable (SRPCOM Download Manager.exe)...
.\.venv\Scripts\pyinstaller.exe --noconsole --onefile --clean --name "SRPCOM Download Manager" --icon "assets/logo.ico" --add-data "assets;assets" --add-data "browser_extension;browser_extension" --collect-all customtkinter --collect-all yt_dlp main.py

if not exist "dist\SRPCOM Download Manager.exe" (
    echo [ERROR] Gagal membuat main executable.
    pause
    exit /b 1
)

echo [2/3] Menyiapkan payload instalasi...
if not exist "payload" mkdir payload
copy /y "dist\SRPCOM Download Manager.exe" "payload\SRPCOM Download Manager.exe" >nul
xcopy /e /i /y "browser_extension" "payload\browser_extension" >nul

echo [3/3] Membangun Unified All-In-One Setup & Uninstaller (SRPCOM_Setup.exe)...
.\.venv\Scripts\pyinstaller.exe --noconsole --onefile --clean --name "SRPCOM_Setup" --icon "assets/logo.ico" --add-data "payload;payload" --add-data "assets;assets" --add-data "browser_extension;browser_extension" --collect-all customtkinter installer.py

echo.
echo =======================================================
echo    BUILD BERHASIL SELESAI!
echo =======================================================
echo File Installer All-in-One: dist\SRPCOM_Setup.exe
echo (Otomatis mode INSTALL jika belum ada, dan mode UNINSTALL jika sudah terpasang)
echo =======================================================
echo.
pause
