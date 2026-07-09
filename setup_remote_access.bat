@echo off
echo ================================================================
echo DAMS REMOTE ACCESS SETUP - NGROK TUNNEL
echo ================================================================
echo.
echo This will create a secure tunnel to make DAMS accessible from anywhere.
echo.
echo Prerequisites:
echo 1. Download ngrok from https://ngrok.com/download
echo 2. Sign up for free account at https://ngrok.com/signup
echo 3. Extract ngrok.exe to this folder
echo.
pause

if not exist "ngrok.exe" (
    echo.
    echo ERROR: ngrok.exe not found in this directory!
    echo Please download ngrok from https://ngrok.com/download
    echo and place ngrok.exe in this folder.
    echo.
    pause
    exit /b 1
)

echo.
echo Starting DAMS server...
start /min python DC_Manager.py --web

timeout /t 3 /nobreak >nul

echo.
echo Creating secure tunnel with ngrok...
echo.
ngrok http 5000

pause
