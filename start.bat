@echo off
cd /d "%~dp0"

echo Activating Conda environment 'bma_cctv'...
call conda activate bma_cctv
if %errorlevel% neq 0 (
    echo Failed to activate Conda environment. Please make sure Conda is installed and the 'bma_cctv' environment exists.
    pause
    exit /b %errorlevel%
)

echo Starting backend server...
bun run .\src\backend.js
if %errorlevel% neq 0 (
    echo Server exited with an error. Error code: %errorlevel%
)

echo.
echo Server stopped. Press any key to exit.
pause >nul