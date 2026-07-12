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

copy /y "README.md" "dist\%APP_NAME%\README.md" >nul
copy /y "USER_GUIDE.md" "dist\%APP_NAME%\USER_GUIDE.md" >nul
copy /y "CHANGELOG.md" "dist\%APP_NAME%\CHANGELOG.md" >nul
copy /y "THIRD_PARTY_NOTICES.md" "dist\%APP_NAME%\THIRD_PARTY_NOTICES.md" >nul
copy /y "KNOWN_ISSUES.md" "dist\%APP_NAME%\KNOWN_ISSUES.md" >nul
copy /y "RELEASE_CHECKLIST.md" "dist\%APP_NAME%\RELEASE_CHECKLIST.md" >nul
copy /y "scripts\register_file_associations.ps1" "dist\%APP_NAME%\register_file_associations.ps1" >nul
copy /y "scripts\unregister_file_associations.ps1" "dist\%APP_NAME%\unregister_file_associations.ps1" >nul

echo.
echo Build finished:
echo %CD%\dist\%APP_NAME%\%APP_NAME%.exe
exit /b 0
