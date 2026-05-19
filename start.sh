#!/bin/bash

# MatchaMind Startup Script
# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🍵 MatchaMind - Smart Lifestyle & Expense Companion${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check Python version
echo -e "\n${YELLOW}📌 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if (( $(echo "$python_version < 3.8" | bc -l) )); then
    echo -e "${RED}❌ Error: Python 3.8+ required (found $python_version)${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $python_version found${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Install/update dependencies
echo -e "\n${YELLOW}📥 Installing dependencies...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "\n${RED}⚠️  Warning: .env file not found!${NC}"
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cat > .env << EOL
# OpenAI Configuration
OPENAI_API_KEY=your_key_here

# App Configuration
DEMO_MODE=true
DEBUG=true

# Supabase (optional)
SUPABASE_URL=
SUPABASE_KEY=
EOL
    echo -e "${RED}❌ Please edit .env file with your API keys first!${NC}"
    echo -e "${YELLOW}Open .env and add your OPENAI_API_KEY${NC}"
    exit 1
fi

# Check for OpenAI API key
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_key_here" ]; then
    echo -e "\n${RED}❌ Error: OPENAI_API_KEY not set in .env file${NC}"
    echo -e "${YELLOW}Please add your OpenAI API key to .env file${NC}"
    exit 1
fi
echo -e "${GREEN}✅ OpenAI API key found${NC}"

# Kill any existing processes on ports
echo -e "\n${YELLOW}🔍 Checking ports...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null
echo -e "${GREEN}✅ Ports cleared${NC}"

# Start backend in background
echo -e "\n${YELLOW}🚀 Starting backend server...${NC}"
cd backend
uvicorn main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to initialize
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi
echo -e "${GREEN}✅ Backend health check passed${NC}"

# Start frontend
echo -e "\n${YELLOW}🎨 Starting frontend...${NC}"
cd frontend
streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"

# Display success message
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ MatchaMind is now running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📱 Frontend:${NC}   http://localhost:8501"
echo -e "${BLUE}🔧 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}📚 API Docs:${NC}   http://localhost:8000/docs"
echo -e "${BLUE}❤️  Health Check:${NC} http://localhost:8000/health"
echo -e "\n${YELLOW}💡 Press Ctrl+C to stop all services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Handle shutdown
shutdown() {
    echo -e "\n${YELLOW}🛑 Shutting down MatchaMind...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

trap shutdown SIGINT SIGTERM

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID