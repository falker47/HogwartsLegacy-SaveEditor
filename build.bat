@echo off
setlocal
echo ========================================
echo  Hogwarts Legacy Save Editor - Dev Build
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found. Install Node.js 20+.
    exit /b 1
)

if not exist "assets\hlsaves.exe" (
    echo Acquiring pinned hlsavetool dependency...
    powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\fetch_hlsaves.ps1"
    if errorlevel 1 exit /b 1
)

echo [1/5] Installing development dependencies...
python -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1

echo [2/5] Running tests...
python -m pytest tests -q
if errorlevel 1 exit /b 1

echo [3/5] Building embedded editor...
pushd HLSE-src
call npm ci
if errorlevel 1 (
    popd
    exit /b 1
)
call npm run build
if errorlevel 1 (
    popd
    exit /b 1
)
popd
copy /Y "HLSE-src\dist\client\index.html" "assets\HLSGE.html" >nul
if errorlevel 1 exit /b 1

echo [4/5] Locating tkinterdnd2...
set TKDND_PATH=
for /f "delims=" %%i in ('python -c "import tkinterdnd2, os; print(os.path.dirname(tkinterdnd2.__file__))"') do set TKDND_PATH=%%i

if "%TKDND_PATH%"=="" (
    set TKDND_ARGS=
) else (
    set TKDND_ARGS=--add-data "%TKDND_PATH%;tkinterdnd2"
)

echo [5/5] Building executable...
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "HogwartsLegacy-SaveEditor" ^
    %TKDND_ARGS% ^
    --add-data "src;src" ^
    --add-data "assets;assets" ^
    --hidden-import=webview ^
    --hidden-import=webview.platforms.edgechromium ^
    --hidden-import=src.config ^
    --hidden-import=src.utils ^
    --hidden-import=src.editor ^
    --hidden-import=src.app ^
    main.py
if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\HogwartsLegacy-SaveEditor.exe
echo oo2core_9_win64.dll is intentionally not copied or packaged.
endlocal
