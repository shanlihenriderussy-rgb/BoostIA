@echo off
setlocal

echo ========================================
echo  BoostIA - Installation Locale
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non trouve.
    echo Veuillez installer Python 3.11+ depuis https://python.org
    pause
    exit /b 1
)

echo [OK] Python detecte

REM Check Ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [AVERT] Ollama ne semble pas demarre.
    echo Veuillez installer Ollama : https://ollama.com
    echo.
    echo Appuyez sur une touche pour continuer quand Ollama sera pret...
    pause
)

echo [OK] Ollama detecte

REM Create venv if not exists
if not exist ".venv" (
    echo.
    echo [1/4] Creation de l'environnement virtuel...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERREUR] Echec creation venv
        pause
        exit /b 1
    )
)

echo [OK] Environment virtuel pret

REM Activate venv
call .venv\Scripts\activate.bat

echo.
echo [2/4] Installation des dependances...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Echec installation dependances
    pause
    exit /b 1
)

echo [OK] Dependances installees

REM Download phi4 if not exists
echo.
echo [3/4] Verification du modele phi4...
ollama list | findstr /C:"phi4" >nul 2>&1
if errorlevel 1 (
    echo Telechargement de phi4 (cela peut prendre quelques minutes)...
    ollama pull phi4
)

echo [OK] Modele pret

REM Copy .env if not exists
if not exist ".env" (
    echo.
    echo [4/4] Configuration...
    copy .env.example .env
)

echo.
echo ========================================
echo  Installation terminee !
echo ========================================
echo.
echo Pour demarrer BoostIA :
echo   .venv\Scripts\activate.bat
echo   uvicorn app.main:app --port 8000
echo.
echoPuis ouvrez http://localhost:8000 dans votre navigateur.
echo.
pause