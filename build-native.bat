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
    echo [WARNING] Visual Studio developer cmd not found at preset locations. We'll try to detect Visual Studio with vswhere or fall back to a single-config Release build.
)
for /f "usebackq delims=" %%I in (`"%VENV%\Scripts\python.exe" -m pybind11 --cmakedir`) do set "PYBIND11_DIR=%%I"

rem Remove previous CMake configuration to ensure a clean regenerate
if exist "%ROOT%\build" (
    echo Cleaning previous CMake configuration in %ROOT%\build ...
    rd /s /q "%ROOT%\build"
)

rem Detect Visual Studio with vswhere and prefer the correct Visual Studio generator when available.
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" set "VSWHERE=%ProgramFiles%\Microsoft Visual Studio\Installer\vswhere.exe"

if exist "%VSWHERE%" (
    "%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath > "%ROOT%\vswhere_out.txt" 2>nul
    if exist "%ROOT%\vswhere_out.txt" for /f "usebackq delims=" %%V in ("%ROOT%\vswhere_out.txt") do set "VS_INSTALL_PATH=%%~fV"
    if exist "%ROOT%\vswhere_out.txt" del "%ROOT%\vswhere_out.txt" >nul 2>&1

    "%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationVersion > "%ROOT%\vswhere_version.txt" 2>nul
    if exist "%ROOT%\vswhere_version.txt" for /f "usebackq delims=" %%V in ("%ROOT%\vswhere_version.txt") do set "VS_INSTALL_VERSION=%%~V"
    if exist "%ROOT%\vswhere_version.txt" del "%ROOT%\vswhere_version.txt" >nul 2>&1
)

set "VS_GENERATOR=Visual Studio 17 2022"
if defined VS_INSTALL_VERSION (
    if "%VS_INSTALL_VERSION:~0,2%"=="18" set "VS_GENERATOR=Visual Studio 18 2026"
    if "%VS_INSTALL_VERSION:~0,2%"=="17" set "VS_GENERATOR=Visual Studio 17 2022"
    if "%VS_INSTALL_VERSION:~0,2%"=="16" set "VS_GENERATOR=Visual Studio 16 2019"
)
if defined VS_INSTALL_PATH goto :USE_VS

rem Fallback: configure single-config Release (requires nmake or appropriate toolchain in PATH)
echo Visual Studio not detected; configuring single-config Release. Ensure you have a compatible build tool (nmake or make) in PATH.
"%VENV%\Scripts\cmake.exe" -S "%ROOT%" -B "%ROOT%\build" -DPython_EXECUTABLE="%VENV%\Scripts\python.exe" -Dpybind11_DIR="%PYBIND11_DIR%" -DCMAKE_BUILD_TYPE=Release
if errorlevel 1 exit /b %errorlevel%

echo Building native extension (single-config, Release)...
"%VENV%\Scripts\cmake.exe" --build "%ROOT%\build"
if errorlevel 1 exit /b %errorlevel%

goto :EOF

:USE_VS
echo Detected Visual Studio at %VS_INSTALL_PATH%; configuring Visual Studio generator %VS_GENERATOR%.
"%VENV%\Scripts\cmake.exe" -S "%ROOT%" -B "%ROOT%\build" -G "%VS_GENERATOR%" -A x64 -DPython_EXECUTABLE="%VENV%\Scripts\python.exe" -Dpybind11_DIR="%PYBIND11_DIR%"
if errorlevel 1 exit /b %errorlevel%

echo Building native extension (Release) with Visual Studio generator...
"%VENV%\Scripts\cmake.exe" --build "%ROOT%\build" --config Release
if errorlevel 1 exit /b %errorlevel%
