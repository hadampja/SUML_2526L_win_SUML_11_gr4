@echo off
setlocal
cd /d "%~dp0"

REM Bypass dotyczy tylko tego uruchomienia PowerShella.
REM Nie zmienia trwale polityki wykonywania skryptow w Windows.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_windows.ps1"

if errorlevel 1 (
    echo.
    echo Uruchamianie aplikacji zakonczylo sie bledem.
    pause
    exit /b 1
)

endlocal
