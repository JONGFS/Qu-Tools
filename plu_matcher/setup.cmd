@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "VIRTUAL_ENVIRONMENT=%PROJECT_ROOT%.venv"
set "VIRTUAL_PYTHON=%VIRTUAL_ENVIRONMENT%\Scripts\python.exe"

pushd "%PROJECT_ROOT%" >nul
if errorlevel 1 (
    echo ERROR: Could not open the QU Tools directory. 1>&2
    exit /b 1
)

if exist "%VIRTUAL_PYTHON%" goto verify_python

where py >nul 2>&1
if errorlevel 1 goto try_python_command

py -3 -m venv "%VIRTUAL_ENVIRONMENT%"
if errorlevel 1 (
    set "SETUP_ERROR=Could not create the local Python environment with py."
    goto failed
)
goto verify_python

:try_python_command
where python >nul 2>&1
if errorlevel 1 (
    set "SETUP_ERROR=Python 3.11 or newer was not found on PATH."
    goto failed
)

python -m venv "%VIRTUAL_ENVIRONMENT%"
if errorlevel 1 (
    set "SETUP_ERROR=Could not create the local Python environment with python."
    goto failed
)

:verify_python
"%VIRTUAL_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    set "SETUP_ERROR=QU Tools requires Python 3.11 or newer."
    goto failed
)

"%VIRTUAL_PYTHON%" -m pip install -e ".[dev]"
if errorlevel 1 (
    set "SETUP_ERROR=Could not install QU Tools dependencies. Check package-index access and retry."
    goto failed
)

if not exist "inputs" mkdir "inputs"
if errorlevel 1 (
    set "SETUP_ERROR=Could not create the inputs directory."
    goto failed
)

if exist ".env" goto ensure_demo
copy /Y ".env.example" ".env" >nul
if errorlevel 1 (
    set "SETUP_ERROR=Could not create .env from .env.example."
    goto failed
)
echo.
echo Created .env from .env.example.
echo Add the approved QU credentials before making a live request.

:ensure_demo
if not exist "inputs\Aloha_Qu_Menu_Demo.xlsx" goto create_demo
if not exist "cache\99999-1-1\menu.json" goto create_demo
goto run_tests

:create_demo
"%VIRTUAL_PYTHON%" -m scripts.create_demo_data --force
if errorlevel 1 (
    set "SETUP_ERROR=Could not create the sanitized offline demo data."
    goto failed
)

:run_tests
"%VIRTUAL_PYTHON%" -m pytest -q
if errorlevel 1 (
    set "SETUP_ERROR=Setup completed, but the test suite failed."
    goto failed
)

echo.
echo Setup complete.
echo Offline demo: .\run.cmd run --location demo --offline
echo Next: .\run.cmd status --location atlanta
popd >nul
endlocal
exit /b 0

:failed
echo ERROR: %SETUP_ERROR% 1>&2
popd >nul
endlocal
exit /b 1
