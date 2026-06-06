@echo off
chcp 65001 >nul
setlocal

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    echo         Check: Add Python to PATH
    pause
    exit /b 1
)

set SCRIPT_DIR=%~dp0

net session >nul 2>&1
if %errorlevel% == 0 (
    python "%SCRIPT_DIR%ShareWizard.py"
) else (
    powershell -Command "Start-Process -FilePath python -ArgumentList '\"%SCRIPT_DIR%ShareWizard.py\"' -Verb RunAs"
)

endlocal
