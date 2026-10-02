@echo off
title Adaptive Image Optimizer - Web Interface
cd /d "%~dp0"

set PYTHONDONTWRITEBYTECODE=1
set PYTHONUNBUFFERED=1
set "PYTHONPATH=%~dp0;%~dp0runtime\Lib\site-packages;%PYTHONPATH%"

:: 1. Prioritize self-contained portable runtime
if exist "%~dp0runtime\python.exe" (
    "%~dp0runtime\python.exe" -B launch_gui.py --web %*
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo Application exited with error code %ERRORLEVEL%.
        pause
    )
    goto :eof
)

:: 2. Fallback to system Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python launch_gui.py --web %*
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo Application exited with error code %ERRORLEVEL%.
        pause
    )
    goto :eof
)

echo.
echo Python was not found. Please install Python or keep the bundled runtime folder.
echo.
pause
