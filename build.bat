@echo off
echo ========================================
echo  Hogwarts Legacy Save Manager - Builder
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

:: Install dependencies
echo [1/4] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

:: Find tkinterdnd2 path
echo.
echo [2/4] Locating libraries...
for /f "delims=" %%i in ('python -c "import tkinterdnd2; import os; print(os.path.dirname(tkinterdnd2.__file__))"') do set TKDND_PATH=%%i

:: Build
echo.
echo [3/4] Building executable...
pyinstaller --onefile --windowed ^
    --name "HL_Save_Manager" ^
    --add-data "%TKDND_PATH%;tkinterdnd2" ^
    --hidden-import=webview ^
    --hidden-import=webview.platforms.edgechromium ^
    main.py

:: Copy files
echo.
echo [4/4] Copying required files...
if not exist dist mkdir dist
copy /Y hlsaves.exe dist\ >nul 2>&1
copy /Y oo2core_9_win64.dll dist\ >nul 2>&1
copy /Y HLSGE.html dist\ >nul 2>&1

echo.
echo ========================================
echo  Build complete!
echo ========================================
echo.
echo Files in 'dist' folder:
echo   - HL_Save_Manager.exe
echo   - hlsaves.exe
echo   - oo2core_9_win64.dll
echo   - HLSGE.html
echo.
pause
