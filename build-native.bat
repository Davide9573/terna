@echo off
setlocal

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "VENV=%ROOT%\.venv"

rem Prefer Visual Studio 2022 Build Tools, fall back to common VS2022/VS2023 IDE locations.
set "VSDEVCMD=C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
if not exist "%VSDEVCMD%" (
    set "VSDEVCMD=C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\Tools\VsDevCmd.bat"
)
if not exist "%VSDEVCMD%" (
    set "VSDEVCMD=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
)
if not exist "%VSDEVCMD%" (
    set "VSDEVCMD=C:\Program Files (x86)\Microsoft Visual Studio\2022\Professional\Common7\Tools\VsDevCmd.bat"
)
if not exist "%VSDEVCMD%" (
    set "VSDEVCMD=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat"
)

if not exist "%VENV%\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found: %VENV%
    exit /b 1
)
if not exist "%VSDEVCMD%" (
    echo [ERROR] Visual Studio C++ developer environment not found. Please install "Build Tools for Visual Studio 2022" or update VSDEVCMD path in this script.
    exit /b 1
)

call "%VSDEVCMD%" -arch=x64 >nul 2>&1
for /f "usebackq delims=" %%I in (`"%VENV%\Scripts\python.exe" -m pybind11 --cmakedir`) do set "PYBIND11_DIR=%%I"

"%VENV%\Scripts\cmake.exe" -S "%ROOT%" -B "%ROOT%\build" -DPython_EXECUTABLE="%VENV%\Scripts\python.exe" -Dpybind11_DIR="%PYBIND11_DIR%"
if errorlevel 1 exit /b %errorlevel%
"%VENV%\Scripts\cmake.exe" --build "%ROOT%\build" --config Release