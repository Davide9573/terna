@echo off
setlocal

set "VENV_DIR=%~dp0.venv"
set "FRONTEND_DIR=%~dp0frontend"

echo === Simulatore Energetico TERNA 2025 ===
echo.

:: Check Node.js
for /f "delims=" %%I in ('where.exe node 2^>nul') do (
    set "NODE_EXE=%%~fI"
    goto :node_found
)

echo [ERRORE] Node.js non trovato nel PATH di sistema.
echo         Installare Node.js e assicurarsi che la sua cartella sia nel PATH.
pause
exit /b 1

:node_found
for %%I in ("%NODE_EXE%") do set "NODE_DIR=%%~dpI"
set "PATH=%NODE_DIR%;%PATH%"

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

echo [2/2] Avvio frontend Vite su http://localhost:5174 ...
start "TERNA Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev -- --strictPort"

:: Attesa per dare tempo al frontend di avviarsi completamente
timeout /t 4 /nobreak >nul

echo [3/3] Apertura del browser a http://localhost:5174/ ...
start http://localhost:5174/

echo.
echo Entrambi i server sono stati avviati in finestre separate.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5174
echo   Browser:  http://localhost:5174/
echo   API docs: http://localhost:8000/docs
echo.
echo Chiudere le rispettive finestre per fermare i server.
pause
