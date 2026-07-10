@echo off
setlocal

cd /d "%~dp0"

set "APP_NAME=FreakMediaPlayer"

call scripts\prepare_build_env.bat fast
if errorlevel 1 exit /b 1

powershell -NoProfile -Command ^
    "$target = [IO.Path]::GetFullPath('%CD%\dist-dev\%APP_NAME%\%APP_NAME%.exe'); $running = @(Get-Process '%APP_NAME%' -ErrorAction SilentlyContinue).Where({$_.Path -eq $target}); if ($running) { exit 1 }"
if errorlevel 1 (
    echo Close the running developer build before rebuilding.
    exit /b 1
)

echo Building fast developer executable...
"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --distpath "%CD%\dist-dev" ^
    --workpath "%CD%\build-dev" ^
    "FreakMediaPlayer.dev.spec"
if errorlevel 1 exit /b 1

echo.
echo Fast build finished:
echo %CD%\dist-dev\%APP_NAME%\%APP_NAME%.exe
exit /b 0
