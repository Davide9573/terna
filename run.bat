@echo off
setlocal

set "VENV_DIR=%~dp0.venv"
set "FRONTEND_DIR=%~dp0frontend"
set "NATIVE_MODULE_DIR=%~dp0build\python\Release"

echo === Simulatore Energetico TERNA 2025 ===
echo.

:: Individua Node.js anche quando non e' nel PATH.
set "NODE_EXE="
for %%I in (
    "%~dp0..\nodejs\node.exe"
    "%~dp0nodejs\node.exe"
    "%ProgramFiles%\nodejs\node.exe"
    "%ProgramFiles(x86)%\nodejs\node.exe"
    "%LocalAppData%\Programs\nodejs\node.exe"
) do (
    if not defined NODE_EXE if exist "%%~fI" set "NODE_EXE=%%~fI"
)

if not defined NODE_EXE (
    for /f "delims=" %%I in ('where.exe node 2^>nul') do (
        if not defined NODE_EXE set "NODE_EXE=%%~fI"
    )
)

if defined NODE_EXE goto :node_found

echo [ERRORE] Node.js non trovato.
echo         Cercato accanto al progetto e nelle cartelle di installazione standard.
echo         Installare Node.js oppure collocare node.exe in ..\nodejs.
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

set "TERNA_SIMULATION_ENGINE=cpp"
set "PYTHONPATH=%NATIVE_MODULE_DIR%;%PYTHONPATH%"
"%VENV_DIR%\Scripts\python.exe" -c "import _terna_cpp; print('[OK] Backend C++:', _terna_cpp.__file__)"
if errorlevel 1 (
    echo [ERRORE] Il backend C++ non e' disponibile.
    echo         Eseguire build-native.bat e verificare che _terna_cpp sia compilato in %NATIVE_MODULE_DIR%.
    pause
    exit /b 1
)

set "PATH=%NODE_DIR%;%PATH%"

echo [1/2] Avvio backend FastAPI su http://localhost:8000 ...
start "TERNA Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload"

:: Breve attesa per dare tempo al backend di avviarsi
timeout /t 3 /nobreak >nul

echo [2/2] Avvio frontend Vite su http://localhost:5174 ...
start "TERNA Frontend" /d "%FRONTEND_DIR%" cmd /k ""%NODE_DIR%npm.cmd" run dev -- --strictPort"

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
