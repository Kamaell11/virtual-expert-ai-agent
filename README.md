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

## Quick Start with Docker

1. **Clone and navigate to project:**
   ```bash
   cd ai_agent
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Download AI model (first run only):**
   ```bash
   docker exec ai_agent_ollama ollama pull llama3.2:1b
   ```

4. **Access the application:**
   - 🌐 Web Interface: http://localhost
   - 📊 Dashboard: http://localhost/dashboard  
   - 💬 Chat: http://localhost/chat
   - 📚 API Documentation: http://localhost/docs

## Local Development Setup

### Backend Setup

1. **Create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export DATABASE_URL="sqlite:///./app.db"  # For testing
   export SECRET_KEY="your-secret-key-here"
   export OLLAMA_BASE_URL="http://localhost:11434"
   ```

4. **Start Ollama (required for LLM functionality):**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama serve
   ollama pull llama2  # Or any preferred model
   ```

5. **Run backend:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set environment variables:**
   ```bash
   # Create .env file
   echo "REACT_APP_API_URL=http://localhost:8000" > .env
   ```

3. **Start development server:**
   ```bash
   npm start
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