@echo off
setlocal

cd /d "%~dp0"

set "APP_NAME=FreakMediaPlayer"
set "VENV_DIR=.venv-build"

py -3.11 -c "import sys" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PY_BOOTSTRAP=py -3.11"
) else (
    py -c "import sys" >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PY_BOOTSTRAP=py"
    ) else (
        python -c "import sys" >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            set "PY_BOOTSTRAP=python"
        ) else (
            if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
                set "PY_BOOTSTRAP=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
            ) else (
                echo Python 3.11 or newer was not found.
                echo Install Python from https://www.python.org/downloads/ and try again.
                echo If you use the Python Launcher, run: py install 3.11
                exit /b 1
            )
        )
    )
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating build environment...
    %PY_BOOTSTRAP% -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1
)

set "PYTHON=%CD%\%VENV_DIR%\Scripts\python.exe"

echo Installing build dependencies...
"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%PYTHON%" -m pip install -e ".[build]"
if errorlevel 1 exit /b 1

echo Building %APP_NAME%.exe...
"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name "%APP_NAME%" ^
    --paths "%CD%\src" ^
    --collect-all PySide6 ^
    "src\freak_media_player\main.py"
if errorlevel 1 exit /b 1

echo.
echo Build finished:
echo %CD%\dist\%APP_NAME%\%APP_NAME%.exe
exit /b 0
