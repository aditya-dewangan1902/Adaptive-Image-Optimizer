@echo off
title Adaptive Image Optimizer - Standalone Windows Application
cd /d "%~dp0"

echo ====================================================================
echo   Adaptive High-Quality Image Optimization System
echo   Launching Standalone Native Windows Application...
echo   (Bright Minimalist Professional UI, Zero Server Required)
echo ====================================================================

set PYTHONDONTWRITEBYTECODE=1
set PYTHONUNBUFFERED=1
set "PYTHONPATH=%~dp0;%~dp0runtime\Lib\site-packages;%PYTHONPATH%"

:: 1. Prioritize self-contained portable runtime (zero setup / zero requirements on target PC)
if exist "%~dp0runtime\python.exe" (
    echo [*] Using bundled portable runtime...
    "%~dp0runtime\python.exe" -B launch_gui.py %*
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Application exited with error code %ERRORLEVEL%.
        pause
    )
    goto :eof
)

:: 2. Fallback to system Python if runtime folder is not present
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] Using system Python...
    python launch_gui.py %*
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Application exited with error code %ERRORLEVEL%.
        pause
    )
    goto :eof
)

echo.
echo [ERROR] Neither portable runtime nor system Python was found!
echo Please keep the 'runtime' folder alongside launch_gui.bat to run on any PC with zero installation.
echo.
pause
