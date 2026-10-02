@echo off
title Adaptive Image Optimizer - Web Browser Interface
cd /d "%~dp0"

echo ====================================================================
echo   Adaptive High-Quality Image Optimization System
echo   Launching Web Browser Interface...
echo ====================================================================

set PYTHONDONTWRITEBYTECODE=1
set PYTHONUNBUFFERED=1
set "PYTHONPATH=%~dp0;%~dp0runtime\Lib\site-packages;%PYTHONPATH%"

:: 1. Prioritize self-contained portable runtime
if exist "%~dp0runtime\python.exe" (
    echo [*] Using bundled portable runtime...
    "%~dp0runtime\python.exe" -B launch_gui.py --web %*
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Application exited with error code %ERRORLEVEL%.
        pause
    )
    goto :eof
)

:: 2. Fallback to system Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Using system Python...
    python launch_gui.py --web %*
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Application exited with error code %ERRORLEVEL%.
        pause
    )
    goto :eof
)

echo.
echo [ERROR] Neither portable runtime nor system Python was found!
echo.
pause
