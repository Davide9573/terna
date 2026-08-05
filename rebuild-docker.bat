@echo off
setlocal

rem Esegui questo script dalla cartella del progetto per ricostruire completamente il container Docker e avviarlo.
cd /d %~dp0

echo [1/4] Arresto dei servizi Docker Compose esistenti...
docker compose down --remove-orphans
if errorlevel 1 goto error

echo [2/4] Ricostruzione completa dell'immagine Docker per il servizio terna...
docker compose build --no-cache --pull terna
if errorlevel 1 goto error

echo [3/4] Avvio del servizio Docker Compose terna...
docker compose up -d --force-recreate terna
if errorlevel 1 goto error

echo [4/4] Mostro i log del servizio terna. Premi CTRL+C per interrompere.
docker compose logs -f terna

goto end

:error
echo.
echo [ERROR] Il comando Docker è fallito. Controlla l'output precedente.
exit /b 1

:end
endlocal
