@echo off
echo ===============================================
echo    AI AGENT BACKGROUND SERVICE STARTER
echo ===============================================
echo.
echo Starting AI Agent Background Service...
echo This will keep the AI agent online and responsive
echo.
echo Press Ctrl+C to stop the service
echo.
pause

cd /d "%~dp0"
python ai_background_service.py

echo.
echo ===============================================
echo Service has stopped
pause