@echo off
setlocal

cd /d "%~dp0"
call build.bat
if errorlevel 1 exit /b 1

set "RUNTIME=%CD%\dist\FreakMediaPlayer\_internal\PySide6"
if not exist "%RUNTIME%\Qt6Multimedia.dll" goto :missing_audio_runtime
if not exist "%RUNTIME%\QtMultimedia.pyd" goto :missing_audio_runtime
if not exist "%RUNTIME%\plugins\multimedia\windowsmediaplugin.dll" if not exist "%RUNTIME%\plugins\multimedia\ffmpegmediaplugin.dll" goto :missing_audio_runtime

set "TARGET=%CD%\release\FreakMediaPlayer-Portable"
if exist "%TARGET%" rmdir /s /q "%TARGET%"
mkdir "%TARGET%"
xcopy /e /i /y "%CD%\dist\FreakMediaPlayer\*" "%TARGET%\" >nul
type nul > "%TARGET%\portable.flag"

echo Portable package created:
echo %TARGET%
exit /b 0

:missing_audio_runtime
echo ERROR: Portable audio runtime is incomplete: %RUNTIME%
exit /b 1
