#!/bin/bash

# Virtual Expert AI - Development Startup Script
# This script helps start the development environment locally

echo "🚀 Starting Virtual Expert AI Development Environment"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18 or higher.${NC}"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Ollama is not running. Please install and start Ollama:${NC}"
    echo "   1. Install from: https://ollama.ai"
    echo "   2. Run: ollama serve"
    echo "   3. Install a model: ollama pull llama2"
    echo -e "${BLUE}Press any key to continue when Ollama is ready...${NC}"
    read -n 1 -s
fi

echo -e "${BLUE}📦 Setting up backend environment...${NC}"

# Setup backend
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Set environment variables
export DATABASE_URL="sqlite:///./app.db"
export SECRET_KEY="dev-secret-key-change-in-production"
export OLLAMA_BASE_URL="http://localhost:11434"

echo -e "${GREEN}✅ Backend environment ready${NC}"

# Start backend in background
echo "Starting FastAPI backend..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /dev/null 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Setup frontend
cd ../frontend

echo -e "${BLUE}📦 Setting up frontend environment...${NC}"

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install > /dev/null 2>&1
fi

# Create .env file for frontend
echo "REACT_APP_API_URL=http://localhost:8000" > .env

echo -e "${GREEN}✅ Frontend environment ready${NC}"

# Start frontend
echo "Starting React development server..."
npm start > /dev/null 2>&1 &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}🎉 Virtual Expert AI is starting up!${NC}"
echo "================================================="
echo -e "📱 Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "🔧 Backend API: ${BLUE}http://localhost:8000${NC}"
echo -e "📚 API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo "================================================="
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Services stopped successfully${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for services to run
wait