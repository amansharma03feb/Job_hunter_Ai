@echo off
title Setup Daily Job Hunt Schedule
echo ============================================================
echo   Setting up daily 8 AM schedule via Windows Task Scheduler
echo   Owner: Aman Sharma
echo ============================================================
echo.

:: Create scheduled task - runs daily at 8:00 AM
schtasks /create /tn "AI_Job_Hunter_Daily" /tr "\"%~dp0run.bat\"" /sc daily /st 08:00 /f

if %errorlevel%==0 (
    echo.
    echo [SUCCESS] Scheduled task created!
    echo   Name:     AI_Job_Hunter_Daily
    echo   Schedule: Every day at 8:00 AM
    echo   Action:   %~dp0run.bat
    echo.
    echo To manage: Open Task Scheduler or run:
    echo   schtasks /query /tn "AI_Job_Hunter_Daily"
    echo   schtasks /delete /tn "AI_Job_Hunter_Daily" /f  (to remove)
) else (
    echo.
    echo [ERROR] Failed to create scheduled task.
    echo Try running this script as Administrator.
)

echo.
pause
