@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo Cleaning old builds...
rmdir /s /q build
rmdir /s /q dist

echo Building DAMS.exe...
pyinstaller --noconfirm --onedir --windowed --add-data "templates;templates" --add-data "static;static" --add-data "runtime\database;runtime\database" --hidden-import "pandas" --hidden-import "flask" --hidden-import "openpyxl" --hidden-import "sqlite3" --exclude-module "tkinter" --exclude-module "matplotlib" --exclude-module "scipy" --exclude-module "PyQt5" --exclude-module "notebook" --exclude-module "IPython" --name "DAMS" Run.py

echo Build complete! Your DAMS executable is in the 'dist/DAMS' folder.
pause
