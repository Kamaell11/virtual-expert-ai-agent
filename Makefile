# Virtual Expert AI Agent - Makefile
# Simplified commands for development and deployment

.PHONY: help build start stop restart logs clean install dev test

# Default target
help:
	@echo "Virtual Expert AI Agent - Available Commands:"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make install    - Install all dependencies and setup"
	@echo "  make start      - Start all services with Docker"
	@echo "  make dev        - Start development environment"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make build      - Build all Docker containers"
	@echo "  make start      - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - Show container logs"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make dev        - Start local development servers"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean containers and volumes"
	@echo ""
	@echo "🤖 AI Model:"
	@echo "  make model      - Download required AI model"
	@echo "  make model-list - List available models"
	@echo ""
	@echo "📋 System Setup:"
	@echo "  make check-requirements - Check if all tools are installed"
	@echo "  make install-nodejs     - Install Node.js on Ubuntu/Debian"

# Installation and setup
install: install-system-dependencies install-nodejs-if-missing setup-python-venv
	@echo "🔧 Installing dependencies..."
	@echo "📋 Setting up environment files..."
	@cp .env.template .env 2>/dev/null || echo "Main .env already exists"
	@cp backend/.env.template backend/.env 2>/dev/null || echo "Backend .env already exists"  
	@cp frontend/.env.template frontend/.env 2>/dev/null || echo "Frontend .env already exists"
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "📦 Installing backend dependencies..."
	@cd backend && bash -c "source venv/bin/activate && pip install --upgrade pip setuptools wheel"
	@cd backend && bash -c "source venv/bin/activate && pip install --no-cache-dir -r requirements.txt"
	@echo "✅ Dependencies installed successfully!"
	@echo ""
	@echo "⚠️  IMPORTANT: Please edit your .env files with proper values before running the application!"
	@echo "📝 Check .env.template for configuration options"

# Install system dependencies based on OS
install-system-dependencies:
	@echo "🔍 Detecting operating system..."
	@if [ -f /etc/os-release ]; then \
		. /etc/os-release; \
		echo "📋 Detected OS: $$NAME"; \
		if command -v apt-get >/dev/null 2>&1; then \
			echo "📦 Installing system packages (Debian/Ubuntu)..."; \
			sudo apt-get update -qq; \
			sudo apt-get install -y -qq \
				curl \
				wget \
				git \
				build-essential \
				python3 \
				python3-pip \
				python3-venv \
				python3-dev \
				python3-setuptools \
				python3-wheel \
				ca-certificates \
				gnupg \
				lsb-release || true; \
			echo "📋 Trying to install python3-distutils (may not exist in newer Ubuntu)..."; \
			sudo apt-get install -y -qq python3-distutils >/dev/null 2>&1 || echo "⚠️  python3-distutils not available (normal for Python 3.12+)"; \
		elif command -v yum >/dev/null 2>&1; then \
			echo "📦 Installing system packages (CentOS/RHEL/Fedora)..."; \
			sudo yum update -y -q; \
			sudo yum install -y -q \
				curl \
				wget \
				git \
				gcc \
				gcc-c++ \
				make \
				python3 \
				python3-pip \
				python3-devel \
				ca-certificates; \
		elif command -v pacman >/dev/null 2>&1; then \
			echo "📦 Installing system packages (Arch Linux)..."; \
			sudo pacman -Sy --noconfirm --quiet \
				curl \
				wget \
				git \
				base-devel \
				python \
				python-pip \
				ca-certificates; \
		elif command -v apk >/dev/null 2>&1; then \
			echo "📦 Installing system packages (Alpine Linux)..."; \
			sudo apk update -q; \
			sudo apk add --no-cache \
				curl \
				wget \
				git \
				build-base \
				python3 \
				python3-dev \
				py3-pip \
				ca-certificates; \
		else \
			echo "⚠️  Unknown package manager. Please install manually:"; \
			echo "   - curl, wget, git"; \
			echo "   - build tools (gcc, make)"; \
			echo "   - python3, python3-pip, python3-venv"; \
			echo "   - python3-distutils, python3-setuptools"; \
		fi; \
	elif [ "$$(uname)" = "Darwin" ]; then \
		echo "📦 Installing system packages (macOS)..."; \
		if command -v brew >/dev/null 2>&1; then \
			brew update -q; \
			brew install python3 git curl wget; \
		else \
			echo "⚠️  Homebrew not found. Please install:"; \
			echo "   /bin/bash -c \"\$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""; \
			exit 1; \
		fi; \
	else \
		echo "⚠️  Unknown operating system. Please install dependencies manually."; \
	fi
	@echo "✅ System dependencies installed!"

# Auto-install Node.js if missing
install-nodejs-if-missing:
	@if ! command -v node >/dev/null 2>&1; then \
		echo "📦 Node.js not found - installing automatically..."; \
		if command -v apt-get >/dev/null 2>&1; then \
			curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs; \
		elif command -v yum >/dev/null 2>&1; then \
			curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - && sudo yum install -y nodejs; \
		else \
			echo "❌ Cannot auto-install Node.js. Please install manually."; \
			echo "💡 Visit: https://nodejs.org/en/download/"; \
			exit 1; \
		fi; \
		echo "✅ Node.js installed successfully!"; \
		node --version; \
		npm --version; \
	else \
		echo "✅ Node.js already installed ($(node --version))"; \
	fi

# Setup Python virtual environment
setup-python-venv:
	@echo "🐍 Setting up Python virtual environment..."
	@cd backend && (python3 -m venv venv || python -m venv venv)
	@echo "✅ Python virtual environment created!"

# Manual Node.js installation
install-nodejs:
	@echo "📦 Installing Node.js..."
	@if command -v apt-get >/dev/null 2>&1; then \
		curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs; \
	elif command -v yum >/dev/null 2>&1; then \
		curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - && sudo yum install -y nodejs; \
	else \
		echo "❌ Unsupported system. Please install Node.js manually from https://nodejs.org/"; \
		exit 1; \
	fi
	@echo "✅ Node.js installed successfully!"
	@node --version
	@npm --version

# Docker commands
build:
	@echo "🔨 Building Docker containers..."
	@docker-compose build
	@echo "✅ Build completed!"

start:
	@echo "🚀 Starting Virtual Expert AI Agent..."
	@docker-compose up -d
	@echo "✅ Services started!"
	@echo "🌐 Web Interface: http://localhost"
	@echo "📊 API Documentation: http://localhost/docs"

stop:
	@echo "⏹️  Stopping services..."
	@docker-compose down
	@echo "✅ Services stopped!"

restart: stop start

logs:
	@docker-compose logs -f

# AI Model management
model:
	@echo "🤖 Downloading AI model..."
	@docker exec ai_agent_ollama ollama pull llama3.2:1b
	@echo "✅ Model downloaded successfully!"

model-list:
	@echo "📋 Available models:"
	@docker exec ai_agent_ollama ollama list

# Development environment  
dev: setup-python-venv
	@echo "🛠️  Starting development environment..."
	@echo "⚠️  Make sure you have .env files configured (see .env.template)"
	@echo "⚠️  Make sure Ollama is running locally: ollama serve"
	@echo ""
	@echo "📋 Using SQLite database for development (no PostgreSQL required)"
	@echo ""
	@echo "Starting backend in development mode..."
	@cd backend && bash -c "source venv/bin/activate && pip install -r requirements.txt" >/dev/null 2>&1 || true
	@cd backend && bash -c "source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload" &
	@echo "Starting frontend in development mode..."
	@cd frontend && npm install >/dev/null 2>&1 || true
	@cd frontend && npm start &
	@echo "✅ Development servers starting..."
	@echo "🌐 Frontend: http://localhost:3000"
	@echo "🔗 Backend API: http://localhost:8000"
	@echo "📊 API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "💡 To stop development servers: make stop-dev"

# Stop development processes
stop-dev-processes:
	@echo "🛑 Stopping any existing development processes..."
	@-pkill -f "uvicorn main:app" 2>/dev/null || true
	@-pkill -f "react-scripts start" 2>/dev/null || true  
	@-pkill -f "npm start" 2>/dev/null || true
	@sleep 1

# Stop development servers
stop-dev:
	@echo "🛑 Stopping development servers..."
	@-pkill -f "uvicorn main:app" 2>/dev/null || true
	@-pkill -f "react-scripts start" 2>/dev/null || true
	@-pkill -f "npm start" 2>/dev/null || true
	@echo "✅ Development servers stopped!"

# Testing
test: setup-python-venv
	@echo "🧪 Running tests..."
	@cd frontend && npm test
	@cd backend && bash -c "source venv/bin/activate && python -m pytest"
	@echo "✅ Tests completed!"

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@docker system prune -f
	@echo "✅ Cleanup completed!"

# Health check
health:
	@echo "🏥 Checking service health..."
	@curl -s http://localhost/health | jq '.' || echo "❌ Service not responding"

# Quick status
status:
	@echo "📊 Service Status:"
	@docker-compose ps