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
- **🎯 Fine-Tuned Models**: Create specialized AI models for specific domains (medical, legal, mechanic, etc.)
- **📚 Model Management**: Complete fine-tuning pipeline with dataset upload, training, and monitoring
- **🔐 User Isolation**: Secure model access control with permission management between users

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

6. **🎯 Fine-Tuning**: 
   - Create custom AI models specialized for specific domains
   - Upload training datasets (JSONL, CSV, PDF, TXT formats)
   - Monitor training progress with real-time logs and metrics

### 🖥️ System Features
- **📊 Real-time Dashboard**: Statistics, AI status, recent activity
- **📚 Conversation History**: Full chat tracking with search functionality
- **🔐 Secure Authentication**: User accounts with JWT tokens
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **⚡ Live Updates**: Real-time AI responses and system monitoring
- **🎯 Model Management Interface**: Create, train, and manage fine-tuned models
- **📈 Training Progress Monitoring**: Real-time training logs and progress tracking
- **🔄 Real-time Notifications**: Toast notifications for training completion and system events

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
│   ├── datasets/           # Training datasets storage
│   ├── models/             # Fine-tuned models storage
│   │   ├── base/           # Base model cache
│   │   └── fine_tuned/     # User fine-tuned models
│   └── services/          # Service layer
│       ├── auth_service.py # Authentication logic
│       ├── llm_service.py  # Ollama LLM integration
│       ├── fine_tuning_service.py # Model fine-tuning pipeline
│       ├── model_access_service.py # Model access control
│       └── web_search_service.py # DuckDuckGo search integration
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── components/    # Reusable components
│   │   ├── contexts/      # React contexts (Auth, Notifications)
│   │   ├── pages/         # Page components (Chat, Dashboard, Models, etc.)
│   │   ├── services/      # API services
│   │   └── styles/        # CSS styles
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile         # Frontend Docker configuration
├── nginx/                 # Nginx configuration
├── sample_datasets/       # Example training datasets
│   ├── medical_qa.jsonl   # Medical Q&A dataset
│   ├── legal_qa.jsonl     # Legal Q&A dataset
│   └── mechanic_qa.jsonl  # Mechanic Q&A dataset
├── Makefile              # Build and deployment automation
├── start-dev.sh          # Development startup script
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
make stop-dev      # Stop development servers
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
make check-requirements # Check if all tools are installed
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

### Fine-Tuning & Model Management
- `POST /fine-tuning/models` - Create new fine-tuned model
- `GET /fine-tuning/models` - Get user's fine-tuned models
- `POST /fine-tuning/models/{model_id}/datasets` - Upload training dataset
- `POST /fine-tuning/models/{model_id}/train` - Start model training
- `GET /fine-tuning/models/{model_id}/status` - Get training status
- `GET /fine-tuning/models/{model_id}/logs` - Get training logs
- `DELETE /fine-tuning/models/{model_id}` - Delete fine-tuned model
- `GET /fine-tuning/base-models` - Get available base models

### System
- `GET /health` - System health check with AI status
- `GET /models` - Get available AI models
- `GET /` - System information

## Database Models

- **User**: User account information
- **Query**: User queries to the AI
- **Response**: AI responses to queries
- **Agent**: AI agent configurations
- **FineTunedModel**: Custom fine-tuned model definitions
- **TrainingDataset**: Training datasets for fine-tuning
- **FineTuningLog**: Training process logs and metrics
- **UserModelAccess**: Model sharing and access permissions

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

### 🎯 Fine-Tuned Model Creation
```
User: [Creates a medical specialized model through the Models interface]
1. Select "Create New Model" → Choose "DialoGPT-Medium" base model
2. Select "Medical" specialization → Upload medical training datasets
3. Start training process → Monitor real-time progress and logs
4. Use completed model for specialized medical conversations
```

### 🔧 Specialized Domain Interactions
```
User: [Using fine-tuned medical model]
User: "What are the symptoms of Type 2 diabetes?"
AI: "Based on my medical training, Type 2 diabetes symptoms typically include:
     • Increased thirst and frequent urination
     • Fatigue and blurred vision
     • Slow-healing sores and frequent infections
     Please consult with a healthcare professional for proper diagnosis."
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

## 🏗️ Advanced Features

### 🎯 Fine-Tuning Pipeline
- **Model Creation**: Support for multiple base models (DialoGPT, DistilGPT-2)
- **Specializations**: Medical, Legal, Mechanic, Customer Service, General Chat
- **Dataset Support**: JSONL, CSV, PDF, and TXT file formats
- **Training Simulation**: Complete training pipeline with progress monitoring
- **Real-time Logs**: Detailed training logs with metrics (loss, accuracy)

### 🔐 Security & Access Control
- **User Isolation**: Each user's models are completely isolated
- **Model Sharing**: Controlled sharing with permission levels (read/write/admin)
- **Access Expiration**: Time-based access control for shared models
- **Secure File Storage**: Safe handling of uploaded training datasets

### 📊 Monitoring & Analytics
- **Training Progress**: Real-time progress bars and status updates
- **Performance Metrics**: Loss and accuracy tracking during training
- **System Health**: Comprehensive health checks and status monitoring
- **Usage Statistics**: Model usage tracking and analytics

## Development Notes

- The application uses professional security practices with JWT authentication
- All sensitive data is properly handled and not logged
- CORS is configured for cross-origin requests
- The frontend follows React best practices with proper state management
- The backend uses FastAPI's automatic API documentation
- Fine-tuning service implements complete model lifecycle management
- Model access service ensures secure multi-tenant model sharing

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

4. **Fine-Tuning Issues:**
   - Ensure training datasets are in correct format (JSONL recommended)
   - Check dataset validation errors in training logs
   - Verify sufficient disk space for model storage
   
5. **Development Environment:**
   - Use `make stop-dev` to properly stop development servers
   - Check if all dependencies are installed with `make check-requirements`
   - Review environment variables in .env files

## License

This project is created as part of a Master's Thesis on "Creating a Virtual Expert Using LLM" and is intended for educational and research purposes.