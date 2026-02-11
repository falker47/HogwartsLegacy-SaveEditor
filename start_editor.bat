@echo off
echo Starting Hogwarts Legacy Save Editor...

:: Copy the latest frontend build to assets
echo [1/2] Updating frontend assets...
if exist "HLSE-src\dist\client\index.html" (
    copy /Y "HLSE-src\dist\client\index.html" "assets\HLSGE.html" >nul
    if not errorlevel 1 echo    [OK] Frontend assets updated.
) else (
    echo    [!!] WARNING: Built frontend not found in HLSE-src\dist\client\index.html
    echo         Using existing assets/HLSGE.html if available.
)

:: Copy hlsaves.exe to assets
if exist "hlsaves.exe" (
    copy /Y "hlsaves.exe" "assets\hlsaves.exe" >nul
    if not errorlevel 1 echo    [OK] hlsaves.exe copied to assets.
) else (
    echo    [!!] WARNING: hlsaves.exe not found in root folder!
)

:: Find accurate Python command
set PYTHON_CMD=

:: Try Python 3.12 via py launcher (matches build script preference)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py -3.12
    goto launch
)

:: Try default python command
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto launch
)

:: Try py launcher default
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto launch
)

echo ERROR: Python not found. Please install Python 3.12+.
pause
exit /b 1

:launch
echo [2/2] Launching application using: %PYTHON_CMD%
%PYTHON_CMD% main.py

if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%.
    pause
)
