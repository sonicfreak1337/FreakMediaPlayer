@echo off
setlocal

cd /d "%~dp0"

set "APP_NAME=FreakMediaPlayer"
call scripts\prepare_build_env.bat release
if errorlevel 1 exit /b 1

echo Building %APP_NAME%.exe...
"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name "%APP_NAME%" ^
    --paths "%CD%\src" ^
    --collect-all av ^
    --add-data "src\freak_media_player\assets:freak_media_player\assets" ^
    --icon "src\freak_media_player\assets\app_logo.ico" ^
    "src\freak_media_player\main.py"
if errorlevel 1 exit /b 1

echo.
echo Build finished:
echo %CD%\dist\%APP_NAME%\%APP_NAME%.exe
exit /b 0
