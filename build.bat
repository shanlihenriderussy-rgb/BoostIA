@echo off
echo ========================================
echo  BoostIA - Construction .EXE
echo ========================================
echo.
echo Ce script cree un fichier .exe autonome
echo containing l'application complete.
echo.
echo Appuyez sur une touche pour continuer...
pause >nul

REM Activate venv
call .venv\Scripts\activate.bat

REM Install PyInstaller
echo.
echo [1/3] Installation de PyInstaller...
pip install pyinstaller

REM Build .exe
echo.
echo [2/3] Construction du .exe (Cela peut prendre quelques minutes)...
pyinstaller --onefile --name BoostIA --add-data "web;web" --add-data "app;templates" app/main.py

REM Note: We need to modify main.py to serve web files from the bundle
echo.
echo [3/3] Termine !
echo.
echo Le fichier .exe se trouve dans le dossier dist\BoostIA.exe
echo.
pause