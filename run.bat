@echo off
title AI Job Hunter - Aman Sharma

:: Always run from the script's own directory
cd /d "%~dp0"

:: Log file with date stamp
set LOGFILE=output\pipeline_%date:~10,4%%date:~4,2%%date:~7,2%.log

:: Make sure output dir exists
if not exist output mkdir output

echo ============================================================ >> "%LOGFILE%" 2>&1
echo   AI Job Hunter Pipeline - %date% %time% >> "%LOGFILE%" 2>&1
echo ============================================================ >> "%LOGFILE%" 2>&1

:: Try Python 3.13 first (required for JobSpy/numpy)
where py >nul 2>nul
if %errorlevel%==0 (
    echo [*] Running with py -3.13... >> "%LOGFILE%" 2>&1
    py -3.13 -u main.py >> "%LOGFILE%" 2>&1
    if %errorlevel% neq 0 (
        echo [!] py -3.13 failed with exit code %errorlevel% >> "%LOGFILE%" 2>&1
        echo [*] Trying default python... >> "%LOGFILE%" 2>&1
        python -u main.py >> "%LOGFILE%" 2>&1
    )
) else (
    echo [*] Running with default python... >> "%LOGFILE%" 2>&1
    python main.py >> "%LOGFILE%" 2>&1
)

echo. >> "%LOGFILE%" 2>&1
echo Pipeline finished at %time% with exit code %errorlevel% >> "%LOGFILE%" 2>&1
