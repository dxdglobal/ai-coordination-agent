@echo off
echo Starting AI Coordination Agent - Phase 1.3 Semantic Search Demo
echo ================================================================

echo.
echo [1/3] Installing Backend Dependencies...
cd /d "c:\Users\USER\Desktop\Projects\ai-coordination-agent\backend"
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Installing Frontend Dependencies...
cd /d "c:\Users\USER\Desktop\Projects\ai-coordination-agent\frontend"
npm install
if errorlevel 1 (
    echo Error: Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Starting Servers...
echo.
echo Starting Backend Server (Flask)...
start "Backend Server" cmd /k "cd /d c:\Users\USER\Desktop\Projects\ai-coordination-agent\backend && python app.py"

echo.
echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Starting Frontend Server (Vite)...
start "Frontend Server" cmd /k "cd /d c:\Users\USER\Desktop\Projects\ai-coordination-agent\frontend && npm run dev"

echo.
echo ================================================================
echo Both servers are starting up!
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo To test the semantic search:
echo 1. Open http://localhost:5173 in your browser
echo 2. Go to the Tasks page
echo 3. Click the "Semantic Search" tab
echo 4. Try queries like "Find urgent security tasks"
echo.
echo Press any key to run the integration test...
pause

echo.
echo Running Integration Test...
cd /d "c:\Users\USER\Desktop\Projects\ai-coordination-agent"
python test_complete_integration.py

echo.
echo Setup complete! Both servers should be running.
echo Check the opened terminal windows for server status.
pause