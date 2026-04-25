@echo off
echo ================================
echo   Super Agent - Starting...
echo ================================
echo.

echo [1/3] Starting Backend (MySQL)...
start "Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Waiting for backend...
timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ================================
echo   Both services are running!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   DB:       MySQL (my_agent_db)
echo   Admin:    admin / admin123
echo ================================
pause
