@echo off
setlocal
echo Starting Hogwarts Legacy Save Editor...

if not exist "assets\HLSGE.html" (
    echo [!!] assets\HLSGE.html is missing.
    echo      Rebuild it with: cd HLSE-src ^&^& npm ci ^&^& npm run build
    exit /b 1
)

if not exist "assets\hlsaves.exe" (
    echo [!!] assets\hlsaves.exe is missing.
    echo      See THIRD_PARTY_NOTICES.md for upstream provenance.
    exit /b 1
)

set PYTHON_CMD=
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py -3.12
    goto launch
)

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto launch
)

py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto launch
)

echo ERROR: Python not found. Install Python 3.12+.
exit /b 1

:launch
echo Launching with: %PYTHON_CMD%
%PYTHON_CMD% main.py
exit /b %errorlevel%
