@echo off
echo ================================================
echo   Hogwarts Legacy Save Manager - Release Builder
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

:: Create release folder
set RELEASE_DIR=release
if exist %RELEASE_DIR% rmdir /s /q %RELEASE_DIR%
mkdir %RELEASE_DIR%

:: Install dependencies
echo [1/5] Installing dependencies...
pip install -r requirements.txt >nul 2>&1
pip install pyinstaller >nul 2>&1

:: Find tkinterdnd2 path
echo [2/5] Locating libraries...
for /f "delims=" %%i in ('python -c "import tkinterdnd2; import os; print(os.path.dirname(tkinterdnd2.__file__))"') do set TKDND_PATH=%%i

if "%TKDND_PATH%"=="" (
    echo WARNING: tkinterdnd2 not found, building without drag-drop support
    set TKDND_ARGS=
) else (
    set TKDND_ARGS=--add-data "%TKDND_PATH%;tkinterdnd2"
)

:: Build executable
echo [3/5] Building executable...
pyinstaller --onefile --windowed ^
    --name "HL_Save_Manager" ^
    %TKDND_ARGS% ^
    --hidden-import=webview ^
    --hidden-import=webview.platforms.edgechromium ^
    --hidden-import=clr ^
    main.py >nul 2>&1

if not exist dist\HL_Save_Manager.exe (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

:: Copy files to release folder
echo [4/5] Preparing release package...
copy /Y dist\HL_Save_Manager.exe %RELEASE_DIR%\ >nul
copy /Y HLSGE.html %RELEASE_DIR%\ >nul 2>&1
copy /Y hlsaves.exe %RELEASE_DIR%\ >nul 2>&1

:: Create user README
echo [5/5] Creating README...
(
echo ============================================
echo   HOGWARTS LEGACY SAVE MANAGER v1.5
echo   by falker47
echo ============================================
echo.
echo QUICK START:
echo.
echo 1. Copy oo2core_9_win64.dll to this folder
echo    ^(Find it in: [Game]\Engine\Binaries\ThirdParty\Oodle\Win64\^)
echo.
echo 2. Run HL_Save_Manager.exe
echo.
echo 3. Select a save file and click "Edit Save File"
echo.
echo 4. Make your edits and click Download
echo.
echo 5. Done! Your save is updated automatically.
echo.
echo ============================================
echo   REQUIRED FILES
echo ============================================
echo.
echo [x] HL_Save_Manager.exe - This app
echo [x] HLSGE.html - Save editor
echo [x] hlsaves.exe - Compression tool
echo [ ] oo2core_9_win64.dll - YOU MUST ADD THIS!
echo.
echo NOTE: The DLL cannot be distributed. You must
echo copy it from your Hogwarts Legacy installation.
echo.
echo ============================================
echo   CREDITS
echo ============================================
echo.
echo Developer: falker47
echo.
echo Special Thanks:
echo - Katt ^(hlsaves.exe^) - MIT License
echo - ekaomk ^(HLSGE Save Editor^)
echo.
echo ============================================
) > %RELEASE_DIR%\README.txt

:: Check what's missing
echo.
echo ================================================
echo   BUILD COMPLETE!
echo ================================================
echo.
echo Release folder: %RELEASE_DIR%\
echo.
echo Contents:
if exist %RELEASE_DIR%\HL_Save_Manager.exe (echo   [OK] HL_Save_Manager.exe) else (echo   [!!] HL_Save_Manager.exe - MISSING)
if exist %RELEASE_DIR%\HLSGE.html (echo   [OK] HLSGE.html) else (echo   [!!] HLSGE.html - MISSING - Add manually)
if exist %RELEASE_DIR%\hlsaves.exe (echo   [OK] hlsaves.exe) else (echo   [!!] hlsaves.exe - MISSING - Add manually)
echo   [!!] oo2core_9_win64.dll - User must add from game
echo.
echo To create ZIP for distribution:
echo   1. Add any missing files to 'release' folder
echo   2. ZIP the contents of 'release' folder
echo   3. Upload to Nexus Mods / GitHub Releases
echo.
pause
