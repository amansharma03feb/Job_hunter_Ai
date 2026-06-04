@echo off
title AI Job Hunter - Aman Sharma
echo ============================================================
echo   AI Job Hunter - Daily Pipeline v3.1
echo   Owner: Aman Sharma (Proprietary Software)
echo ============================================================
echo.

:: Change to the script's own directory (works from anywhere)
cd /d "%~dp0"

:: Try Python 3.13 first (required for JobSpy/numpy)
where py >nul 2>nul
if %errorlevel%==0 (
    echo [*] Running with Python 3.13...
    py -3.13 main.py
    if %errorlevel% neq 0 (
        echo.
        echo [!] Python 3.13 failed, trying default Python...
        python main.py
    )
) else (
    echo [*] Running with default Python...
    python main.py
)

echo.
echo ============================================================
echo   Pipeline finished. Check Telegram for results.
echo ============================================================
echo.
pause
