@echo off
setlocal
echo ================================================
echo   Hogwarts Legacy Save Editor - Release Builder
echo ================================================
echo.

set PYTHON_CMD=
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py -3.12
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
    ) else (
        py --version >nul 2>&1
        if not errorlevel 1 set PYTHON_CMD=py
    )
)

if "%PYTHON_CMD%"=="" (
    echo ERROR: Python not found. Install Python 3.12+ and retry.
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found. Install Node.js 20+ and retry.
    exit /b 1
)

where powershell >nul 2>&1
if errorlevel 1 (
    echo ERROR: Windows PowerShell is required to acquire the pinned hlsavetool dependency.
    exit /b 1
)

echo [1/7] Acquiring pinned hlsavetool dependency...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\fetch_hlsaves.ps1"
if errorlevel 1 exit /b 1

echo [2/7] Installing Python development dependencies...
%PYTHON_CMD% -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1

echo [3/7] Running Python tests...
%PYTHON_CMD% -m pytest tests -q
if errorlevel 1 exit /b 1

echo [4/7] Building embedded editor...
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

if not exist "HLSE-src\dist\client\index.html" (
    echo ERROR: Frontend build did not produce HLSE-src\dist\client\index.html.
    exit /b 1
)
copy /Y "HLSE-src\dist\client\index.html" "assets\HLSGE.html" >nul
if errorlevel 1 exit /b 1

echo [5/7] Locating tkinterdnd2...
set TKDND_PATH=
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import tkinterdnd2, os; print(os.path.dirname(tkinterdnd2.__file__))"') do set TKDND_PATH=%%i

if "%TKDND_PATH%"=="" (
    echo WARNING: tkinterdnd2 not found; building without bundled drag-and-drop support.
    set TKDND_ARGS=
) else (
    set TKDND_ARGS=--add-data "%TKDND_PATH%;tkinterdnd2"
)

echo [6/7] Building executable...
if exist dist rmdir /s /q dist
%PYTHON_CMD% -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "HogwartsLegacy-SaveEditor" ^
    %TKDND_ARGS% ^
    --add-data "src;src" ^
    --add-data "assets;assets" ^
    --hidden-import=webview ^
    --hidden-import=webview.platforms.edgechromium ^
    --hidden-import=clr ^
    --hidden-import=src.config ^
    --hidden-import=src.utils ^
    --hidden-import=src.editor ^
    --hidden-import=src.app ^
    main.py
if errorlevel 1 exit /b 1

if not exist "dist\HogwartsLegacy-SaveEditor.exe" (
    echo ERROR: PyInstaller did not produce the expected executable.
    exit /b 1
)

echo [7/7] Assembling release package...
set RELEASE_DIR=release
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%\assets"

copy /Y "dist\HogwartsLegacy-SaveEditor.exe" "%RELEASE_DIR%\" >nul
copy /Y "assets\HLSGE.html" "%RELEASE_DIR%\assets\" >nul
copy /Y "assets\hlsaves.exe" "%RELEASE_DIR%\assets\" >nul
copy /Y "assets\editor_bridge.js" "%RELEASE_DIR%\assets\" >nul
copy /Y "LICENSE" "%RELEASE_DIR%\" >nul
copy /Y "CREDITS.md" "%RELEASE_DIR%\" >nul
copy /Y "THIRD_PARTY_NOTICES.md" "%RELEASE_DIR%\" >nul
copy /Y "third_party\hlsavetool-LICENSE.txt" "%RELEASE_DIR%\hlsavetool-LICENSE.txt" >nul

(
echo HOGWARTS LEGACY SAVE EDITOR
echo.
echo 1. Run HogwartsLegacy-SaveEditor.exe.
echo 2. Select a save and choose Edit Save File.
echo 3. Save from the embedded editor to write the edited database back.
echo.
echo hlsaves.exe is pinned to upstream hlsavetool v2.0.1 and acquired during the release build with SHA-256 verification.
echo The Oodle DLL oo2core_9_win64.dll is NOT included.
echo The app first looks for it in supported local game installations.
echo If needed, choose the explicit search/manual-selection path in the app.
echo.
echo Back up important saves before editing.
echo See THIRD_PARTY_NOTICES.md for third-party provenance and license boundaries.
) > "%RELEASE_DIR%\README.txt"

if exist "%RELEASE_DIR%\assets\oo2core_9_win64.dll" (
    echo ERROR: Oodle DLL unexpectedly entered the release package.
    exit /b 1
)

echo.
echo Build complete: %RELEASE_DIR%\
echo Oodle DLL excluded by design.
endlocal
