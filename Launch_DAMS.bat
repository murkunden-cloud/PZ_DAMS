@echo off
title MSEDCL DAMS Portal - Standalone Mode

:: Switch to the correct directory
d:
cd "D:\MYPRO\DC\DC_Manager"

:: Launch the web server
start /min python DC_Manager.py --web

:: Open browser automatically
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5000