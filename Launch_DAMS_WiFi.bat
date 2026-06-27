@echo off
cd /d "%~dp0"

echo.
echo ====================================================================
echo MOBILE WIFI CONNECT (Ensure DAMS Manager is already running first!)
echo ====================================================================
echo.
echo If your mobile phone is connected to the SAME WiFi (or Hotspot) as this laptop,
echo open your mobile browser and type the following link:
echo.

python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print('    http://' + s.getsockname()[0] + ':5000'); s.close()" 2>nul || (
    echo Could not fetch IP automatically. Your IP Addresses:
    ipconfig | findstr "IPv4"
)

echo.
echo ====================================================================
echo Press any key to close this window...
pause >nul
