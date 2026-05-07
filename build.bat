@echo off
setlocal
chcp 65001 >nul

echo ========================================
echo  BoostIA - Construction du .EXE autonome
echo ========================================
echo.

REM Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non trouve. Installez Python 3.11+ depuis https://python.org
    pause
    exit /b 1
)

REM Creer venv si absent
if not exist ".venv" (
    echo [1/5] Creation de l'environnement virtuel...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERREUR] Echec creation venv
        pause
        exit /b 1
    )
) else (
    echo [1/5] Environnement virtuel existant detecte
)

REM Activer venv
call .venv\Scripts\activate.bat

REM Installer toutes les dependances + PyInstaller
echo.
echo [2/5] Installation/MAJ des dependances (peut prendre quelques minutes)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller>=6.0
if errorlevel 1 (
    echo [ERREUR] Echec installation dependances
    pause
    exit /b 1
)

REM Nettoyer build precedent
echo.
echo [3/5] Nettoyage des builds precedents...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build via le .spec
echo.
echo [4/5] Construction du .exe (cela peut prendre 3-5 minutes)...
pyinstaller --clean --noconfirm boostia.spec
if errorlevel 1 (
    echo [ERREUR] Echec PyInstaller
    pause
    exit /b 1
)

echo.
echo [5/5] Termine.
echo.
echo ========================================
echo  BoostIA.exe genere dans : dist\BoostIA.exe
echo ========================================
echo.
echo IMPORTANT : Ollama doit etre installe et en cours d'execution
echo             pour que BoostIA fonctionne. Telechargez-le sur :
echo             https://ollama.com
echo.
echo Au premier lancement, BoostIA tirera le modele par defaut
echo via Ollama (peut prendre quelques minutes selon la connexion).
echo.
pause
