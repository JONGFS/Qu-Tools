@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "VIRTUAL_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

if not exist "%VIRTUAL_PYTHON%" (
    echo ERROR: The local environment is not installed. Run .\setup.cmd first. 1>&2
    exit /b 1
)

pushd "%PROJECT_ROOT%" >nul
if errorlevel 1 (
    echo ERROR: Could not open the QU Tools directory. 1>&2
    exit /b 1
)

"%VIRTUAL_PYTHON%" -m src.cli %*
set "TOOL_EXIT=%ERRORLEVEL%"
popd >nul
endlocal & exit /b %TOOL_EXIT%
