@echo off
setlocal

set "NODE_DIR=D:\Dev\nodejs"
set "VENV_DIR=%~dp0.venv"
set "FRONTEND_DIR=%~dp0frontend"

echo === Simulatore Energetico TERNA 2025 ===
echo.

:: Check Node.js
if not exist "%NODE_DIR%\node.exe" (
    echo [ERRORE] Node.js non trovato in %NODE_DIR%
    echo         Assicurarsi che il percorso sia corretto oppure modificare NODE_DIR in questo script.
    pause
    exit /b 1
)

:: Check venv
if not exist "%VENV_DIR%\Scripts\uvicorn.exe" (
    echo [ERRORE] Virtual environment non trovato in %VENV_DIR%
    echo         Eseguire prima: python -m venv .venv ^&^& .venv\Scripts\pip install fastapi uvicorn[standard]
    pause
    exit /b 1
)

set "PATH=%NODE_DIR%;%PATH%"

echo [1/2] Avvio backend FastAPI su http://localhost:8000 ...
start "TERNA Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload"

:: Breve attesa per dare tempo al backend di avviarsi
timeout /t 3 /nobreak >nul

echo [2/2] Avvio frontend Vite su http://localhost:5173 ...
start "TERNA Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"

:: Attesa per dare tempo al frontend di avviarsi completamente
timeout /t 4 /nobreak >nul

echo [3/3] Apertura del browser a http://localhost:5174/ ...
start http://localhost:5174/

echo.
echo Entrambi i server sono stati avviati in finestre separate.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   Browser:  http://localhost:5174/
echo   API docs: http://localhost:8000/docs
echo.
echo Chiudere le rispettive finestre per fermare i server.
pause
