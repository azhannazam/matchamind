@echo off
echo Installing MatchaMind Dependencies...
echo.

REM Create virtual environment
python -m venv venv

REM Activate
call venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install all dependencies
pip install fastapi==0.104.1 uvicorn==0.24.0 streamlit==1.28.1 pandas==2.1.3 plotly==5.17.0 python-dotenv==1.0.0 requests==2.31.0 pydantic==2.4.2 python-multipart httpx beautifulsoup4 lxml

REM Install AI provider (change this based on your choice)
pip install google-generativeai

REM Install testing tools
pip install pytest pytest-cov

echo.
echo ✅ Installation complete!
echo.
echo Next steps:
echo 1. Create .env file with your API key
echo 2. Run: start.bat
pause