# 🤖 Virtual Expert AI Agent - Master's Thesis Project

A comprehensive AI agent system with advanced capabilities including web search, file generation, data analysis, and natural language processing. Built with modern web technologies and integrated with Ollama for local LLM processing.

## 🎯 Core Architecture

- **🚀 Backend**: FastAPI with async support and SQLAlchemy ORM
- **⚛️ Frontend**: React 18 with Material-UI components  
- **🤖 AI Integration**: Ollama (llama3.2:1b model) for local LLM processing
- **🌐 Web Search**: DuckDuckGo API integration for real-time information
- **🔐 Authentication**: JWT-based secure user authentication
- **🐳 Deployment**: Fully containerized with Docker & Nginx reverse proxy

## ✨ Advanced AI Agent Features

### 🧠 Intelligent Capabilities
- **🌐 Web Search Integration**: Real-time internet search for current information (weather, news, facts)
- **📊 File Generation**: Create and download CSV files with custom data (population, sales, employees)
- **📈 Data Analysis**: Upload and analyze CSV/text files with detailed statistics
- **💬 Natural Conversations**: Context-aware, human-like interactions in multiple languages
- **💾 Chat Export**: Export conversation history to CSV format
- **🔍 Smart Context**: Maintains conversation context and learns from interactions

### 🛠️ AI Agent Tools
The AI agent can perform these actions when requested:

1. **🌦️ Weather Information**: 
   - "What's the weather in Lublin?" → Real-time weather search and response

2. **📊 Data Generation**: 
   - "Generate a CSV with European population data" → Creates downloadable files
   - Sales reports, employee lists, custom datasets

3. **📈 File Analysis**: 
   - Upload CSV/TXT files → Detailed statistical analysis and insights

4. **🌐 Current Information**: 
   - "What's happening today?" → Web search for latest news/events

5. **💾 Data Export**: 
   - Export chat conversations to CSV format

### 🖥️ System Features
- **📊 Real-time Dashboard**: Statistics, AI status, recent activity
- **📚 Conversation History**: Full chat tracking with search functionality
- **🔐 Secure Authentication**: User accounts with JWT tokens
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **⚡ Live Updates**: Real-time AI responses and system monitoring

## Project Structure

```
ai_agent/
├── backend/                 # FastAPI backend application
│   ├── main.py             # FastAPI main application
│   ├── models.py           # SQLAlchemy database models
│   ├── schemas.py          # Pydantic schemas
│   ├── database.py         # Database configuration
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Backend Docker configuration
│   └── services/          # Service layer
│       ├── auth_service.py # Authentication logic
│       └── llm_service.py  # Ollama LLM integration
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── components/    # Reusable components
│   │   ├── contexts/      # React contexts (Auth)
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   └── styles/        # CSS styles
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile         # Frontend Docker configuration
├── nginx/                 # Nginx configuration
└── docker-compose.yml     # Docker orchestration
```

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)

## 🚀 Quick Start with Makefile

### Option 1: One-Command Setup (Recommended)
```bash
# Install everything automatically (Node.js, Python, dependencies)
make install

# Start development servers
make dev
```

### Option 2: Docker Production Environment  
```bash
# Build and start all services
make start

# Download AI model (first run only)
make model
```

### Access the application:
- 🌐 **Frontend**: http://localhost:3000 (dev) or http://localhost (prod)
- 🔗 **Backend API**: http://localhost:8000  
- 📚 **API Documentation**: http://localhost:8000/docs

## 📋 Available Makefile Commands

### 🎯 Essential Commands
```bash
make help          # Show all available commands
make install       # Install all dependencies and setup environment
make dev           # Start development servers (auto-installs dependencies)
make start         # Start production environment with Docker
make stop          # Stop all Docker services
make restart       # Restart all Docker services
```

### 🔧 Development Commands  
```bash
make dev           # Start local development servers
make test          # Run all tests
make logs          # Show Docker container logs
make clean         # Clean up Docker containers and volumes
```

### 🤖 AI Model Management
```bash
make model         # Download required AI model (llama3.2:1b)
make model-list    # List all available models
```

### 📊 System Management
```bash
make status        # Show service status
make health        # Check service health
make install-nodejs # Install Node.js manually (if needed)
```

## 🛠️ Development vs Production

### Development Mode (`make dev`)
- ✅ **Local servers** - Frontend on :3000, Backend on :8000
- ✅ **Hot reload** - Auto-restart on code changes  
- ✅ **Direct debugging** - Full access to logs and debugging
- ✅ **Fast iteration** - Quick testing and development
- ⚠️ **Requires**: Ollama running locally (`ollama serve`)

### Production Mode (`make start`) 
- ✅ **Docker containers** - Isolated, scalable services
- ✅ **Nginx proxy** - Professional reverse proxy setup
- ✅ **Database** - PostgreSQL with persistent storage  
- ✅ **All-in-one** - Complete production environment
- 🌐 **Web Interface**: http://localhost

## 📝 Manual Setup (Advanced Users)

If you prefer manual setup instead of using Makefile:

### Prerequisites Installation
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y curl git build-essential python3 python3-pip python3-venv

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Ollama
curl https://ollama.ai/install.sh | sh
```

### Manual Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Copy and edit environment file
cp .env.template .env
# Edit .env with your configuration

# Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Manual Frontend Setup  
```bash
cd frontend
npm install

# Copy and edit environment file
cp .env.template .env
# Edit .env with your configuration

# Start frontend
npm start
```

### Manual Ollama Setup
```bash
# Start Ollama service
ollama serve

# Download AI model
ollama pull llama3.2:1b
```

## Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing secret
- `OLLAMA_BASE_URL`: Ollama API endpoint (default: http://localhost:11434)
- `ALLOWED_ORIGINS`: CORS allowed origins

### Frontend
- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)

## 🔗 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication

### AI Chat & Queries
- `POST /query` - Send message to AI agent (with web search and tool capabilities)
- `GET /queries` - Get user's conversation history
- `DELETE /queries/{query_id}` - Delete specific conversation

### File Operations
- `POST /files/upload` - Upload file for analysis
- `POST /files/analyze` - Analyze uploaded file with statistics
- `POST /files/generate-csv` - Generate and download CSV files

### Web Search
- `POST /search/web` - Perform web search (used internally by AI agent)

### System
- `GET /health` - System health check with AI status
- `GET /models` - Get available AI models
- `GET /` - System information

## Database Models

- **User**: User account information
- **Query**: User queries to the AI
- **Response**: AI responses to queries
- **Agent**: AI agent configurations

## 💡 Usage Examples

### 💬 Natural Conversations
```
User: "Hi, how are you?"
AI: "Hi there! I'm doing well, thanks for asking. How can I help you today?"
```

### 🌦️ Real-time Weather Information
```
User: "What's the weather in Lublin right now?"
AI: "Let me search for the current weather in Lublin...
     Based on the latest data from weather services, Lublin currently has 
     a temperature of 12°C with partly cloudy conditions..."
```

### 📊 File Generation
```
User: "Generate a CSV file with European population data"
AI: "I'll generate a CSV file with European population data for you!"
     [File automatically downloads: europe_population.csv]
```

### 📈 File Analysis
```
User: [Uploads sales_data.csv]
AI: "I've analyzed your file 'sales_data.csv':
     • 1,247 rows, 5 columns
     • Total sales: $2,891,245
     • Top performing region: North America
     • Average transaction: $2,315"
```

### 🌐 Current Information Search
```
User: "What's happening in Poland today?"
AI: "Let me search for the latest news from Poland...
     [Provides current news and events based on web search results]"
```

## 🛠️ Technology Stack

- **🚀 Backend Framework**: FastAPI with async support
- **🗄️ Database**: PostgreSQL with SQLAlchemy ORM
- **🤖 AI/LLM**: Ollama (llama3.2:1b model, local & free)
- **🌐 Web Search**: DuckDuckGo API integration
- **⚛️ Frontend**: React 18 with Material-UI components
- **🔐 Authentication**: JWT tokens with secure handling
- **🐳 Containerization**: Docker & Docker Compose
- **🌐 Reverse Proxy**: Nginx with SSL support

## Development Notes

- The application uses professional security practices with JWT authentication
- All sensitive data is properly handled and not logged
- CORS is configured for cross-origin requests
- The frontend follows React best practices with proper state management
- The backend uses FastAPI's automatic API documentation

## Troubleshooting

1. **Ollama Connection Issues:**
   - Ensure Ollama is running: `ollama serve`
   - Check if a model is installed: `ollama list`
   - Install a model: `ollama pull llama2`

2. **Database Issues:**
   - Check PostgreSQL connection string
   - Ensure database exists and is accessible

3. **Docker Issues:**
   - Ensure Docker and Docker Compose are installed
   - Check port availability (3000, 8000, 5432, 11434)

## License

This project is created as part of a Master's Thesis on "Creating a Virtual Expert Using LLM" and is intended for educational and research purposes.