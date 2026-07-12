@echo off
setlocal

cd /d "%~dp0"
call build.bat
if errorlevel 1 exit /b 1

set "TARGET=%CD%\release\FreakMediaPlayer-Portable"
if exist "%TARGET%" rmdir /s /q "%TARGET%"
mkdir "%TARGET%"
xcopy /e /i /y "%CD%\dist\FreakMediaPlayer\*" "%TARGET%\" >nul
type nul > "%TARGET%\portable.flag"

echo Portable package created:
echo %TARGET%
exit /b 0
