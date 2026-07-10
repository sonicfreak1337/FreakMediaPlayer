@echo off

set "VENV_DIR=.venv-build"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    call :find_python
    if errorlevel 1 exit /b 1
    echo Creating build environment...
    %PY_BOOTSTRAP% -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1
)

set "PYTHON=%CD%\%VENV_DIR%\Scripts\python.exe"

if /I "%~1"=="fast" (
    "%PYTHON%" -c "import av, numpy, PyInstaller, PySide6, scipy" >nul 2>nul
    if not errorlevel 1 exit /b 0
)

echo Synchronizing build dependencies...
"%PYTHON%" -m pip install -e ".[build]"
exit /b %ERRORLEVEL%

:find_python
py -3.11 -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PY_BOOTSTRAP=py -3.11"
    exit /b 0
)
py -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PY_BOOTSTRAP=py"
    exit /b 0
)
python -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PY_BOOTSTRAP=python"
    exit /b 0
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "PY_BOOTSTRAP=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    exit /b 0
)
echo Python 3.11 or newer was not found.
echo Install Python from https://www.python.org/downloads/ and try again.
echo If you use the Python Launcher, run: py install 3.11
exit /b 1
