@echo off
echo ================================================
echo   Hogwarts Legacy Save Editor - Release Builder
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
python -m PyInstaller --onefile --windowed ^
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
    main.py >nul 2>&1


if not exist dist\HogwartsLegacy-SaveEditor.exe (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

:: Copy files to release folder
echo [4/5] Preparing release package...
copy /Y dist\HogwartsLegacy-SaveEditor.exe %RELEASE_DIR%\ >nul
copy /Y HLSGE.html %RELEASE_DIR%\ >nul 2>&1
copy /Y hlsaves.exe %RELEASE_DIR%\ >nul 2>&1

:: Create user README
echo [5/5] Creating README...
echo ============================================ > %RELEASE_DIR%\README.txt
echo   HOGWARTS LEGACY SAVE EDITOR v1.0 >> %RELEASE_DIR%\README.txt
echo   by falker47 >> %RELEASE_DIR%\README.txt
echo ============================================ >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo QUICK START: >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo 1. FIRST LAUNCH: >> %RELEASE_DIR%\README.txt
echo    Double-click 'HogwartsLegacy-SaveEditor.exe'. >> %RELEASE_DIR%\README.txt
echo    The app will try to AUTO-FIND 'oo2core_9_win64.dll'. >> %RELEASE_DIR%\README.txt
echo    It scans all your Steam/Epic game libraries (e.g. FC26, Hogwarts Legacy). >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
    echo    IF AUTO-DISCOVERY FAILS: >> %RELEASE_DIR%\README.txt
    echo    The app will ask if you want to DOWNLOAD the file automatically. >> %RELEASE_DIR%\README.txt
    echo    - Click "Yes" to DOWNLOAD (from Modding Wiki with hash verification) >> %RELEASE_DIR%\README.txt
    echo    - Click "No" to SEARCH your PC or select the file manually. >> %RELEASE_DIR%\README.txt
    echo    You CANNOT use the app until this file is found/downloaded. >> %RELEASE_DIR%\README.txt
    echo. >> %RELEASE_DIR%\README.txt
    echo    MANUAL DLL SETUP (If download fails): >> %RELEASE_DIR%\README.txt
    echo    Copy 'oo2core_9_win64.dll' from: >> %RELEASE_DIR%\README.txt
    echo    Steam:      C:\Program Files (x86)\Steam\steamapps\common\Hogwarts Legacy\Engine\Binaries\ThirdParty\Oodle\Win64\ >> %RELEASE_DIR%\README.txt
    echo    Epic Games: C:\Program Files\Epic Games\Hogwarts Legacy\Engine\Binaries\ThirdParty\Oodle\Win64\ >> %RELEASE_DIR%\README.txt
    echo    - Copy 'oo2core_9_win64.dll' >> %RELEASE_DIR%\README.txt
    echo    - Paste it into the same folder as this app >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo 2. RUN THE APP: >> %RELEASE_DIR%\README.txt
echo    Double-click 'HogwartsLegacy-SaveEditor.exe' >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo 3. EDIT: >> %RELEASE_DIR%\README.txt
echo    Select a save file, click "Edit Save File", make changes, and click "Download". >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo ============================================ >> %RELEASE_DIR%\README.txt
echo   REQUIRED FILES >> %RELEASE_DIR%\README.txt
echo ============================================ >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo [x] HogwartsLegacy-SaveEditor.exe - This app >> %RELEASE_DIR%\README.txt
echo [x] HLSGE.html - Save editor >> %RELEASE_DIR%\README.txt
echo [x] hlsaves.exe - Compression tool >> %RELEASE_DIR%\README.txt
echo [?] oo2core_9_win64.dll - Auto-detected or manual copy >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo ============================================ >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo NOTE: The DLL cannot be distributed due to license. >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo ============================================ >> %RELEASE_DIR%\README.txt
echo   CREDITS >> %RELEASE_DIR%\README.txt
echo ============================================ >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo Developer: falker47 >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo Special Thanks: >> %RELEASE_DIR%\README.txt
echo - Katt (hlsaves.exe) - MIT License >> %RELEASE_DIR%\README.txt
echo - ekaomk (HLSGE Save Editor) >> %RELEASE_DIR%\README.txt
echo. >> %RELEASE_DIR%\README.txt
echo ============================================ >> %RELEASE_DIR%\README.txt

:: Check what's missing
echo.
echo ================================================
echo   BUILD COMPLETE!
echo ================================================
echo.
echo Release folder: %RELEASE_DIR%\
echo.
echo Contents:
if exist %RELEASE_DIR%\HogwartsLegacy-SaveEditor.exe (echo   [OK] HogwartsLegacy-SaveEditor.exe) else (echo   [!!] HogwartsLegacy-SaveEditor.exe - MISSING)
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
