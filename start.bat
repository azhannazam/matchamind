@echo off
title MatchaMind - Smart Lifestyle & Expense Companion
color 0A

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🍵 MatchaMind - Smart Lifestyle & Expense Companion
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: Check Python version
echo 📌 Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
python --version
echo ✅ Python found

:: Check if virtual environment exists
if not exist "venv" (
    echo.
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
)

:: Activate virtual environment
echo.
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated

:: Install/update dependencies
echo.
echo 📥 Installing dependencies...
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo ✅ Dependencies installed

:: Check for .env file
if not exist ".env" (
    echo.
    echo ⚠️  Warning: .env file not found!
    echo Creating .env from template...
    (
        echo # OpenAI Configuration
        echo OPENAI_API_KEY=your_key_here
        echo.
        echo # App Configuration
        echo DEMO_MODE=true
        echo DEBUG=true
        echo.
        echo # Supabase (optional)
        echo SUPABASE_URL=
        echo SUPABASE_KEY=
    ) > .env
    echo.
    echo ❌ Please edit .env file with your API keys first!
    echo Open .env and add your OPENAI_API_KEY
    pause
    exit /b 1
)

:: Check for OpenAI API key
findstr /C:"your_key_here" .env >nul
if not errorlevel 1 (
    echo.
    echo ❌ Error: OPENAI_API_KEY not set in .env file
    echo Please add your OpenAI API key to .env file
    pause
    exit /b 1
)
echo ✅ OpenAI API key found

:: Kill any existing processes on ports
echo.
echo 🔍 Checking ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo ✅ Ports cleared

:: Start backend in background
echo.
echo 🚀 Starting backend server...
start "MatchaMind Backend" /MIN cmd /c "cd backend && uvicorn main:app --reload --port 8000 --host 0.0.0.0"
echo ✅ Backend started

:: Wait for backend to initialize
echo ⏳ Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

:: Check if backend is running
echo 🔍 Checking backend health...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend failed to start
    pause
    exit /b 1
)
echo ✅ Backend health check passed

:: Start frontend
echo.
echo 🎨 Starting frontend...
start "MatchaMind Frontend" cmd /k "cd frontend && streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0"

:: Display success message
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ✅ MatchaMind is now running!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📱 Frontend:   http://localhost:8501
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs:   http://localhost:8000/docs
echo ❤️  Health Check: http://localhost:8000/health
echo.
echo 💡 Two windows opened:
echo    - Backend window (minimized)
echo    - Frontend window (shows Streamlit)
echo.
echo 🔴 To stop: Close both terminal windows
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
pause