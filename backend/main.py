from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import os
import io
import json
import pandas as pd
from typing import Optional
from dotenv import load_dotenv

from database import SessionLocal, engine
from models import Base, User, Query, Response
from schemas import UserCreate, QueryCreate, QueryResponse, UserResponse
from services.llm_service import LLMService
from services.auth_service import AuthService
from services.web_search_service import WebSearchService

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Virtual Expert AI Agent",
    description="A professional virtual expert system using LLM for automated assistance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
auth_service = AuthService()
llm_service = LLMService()
web_search_service = WebSearchService()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    return auth_service.get_current_user(credentials.credentials, db)

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Virtual Expert AI Agent API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check LLM service
        llm_status = await llm_service.health_check()
        return {
            "status": "healthy",
            "services": {
                "api": "online",
                "llm": "online" if llm_status else "offline",
                "database": "online"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    return auth_service.create_user(user, db)

@app.post("/auth/login")
async def login(user: UserCreate, db: Session = Depends(get_db)):
    """Login user and get access token"""
    return auth_service.authenticate_user(user, db)

@app.post("/query", response_model=QueryResponse)
async def create_query(
    query: QueryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process user query and generate AI response"""
    try:
        # Get AI agent response with tool capabilities
        ai_response = await llm_service.create_agent_response(query.query_text, web_search_service=web_search_service)
        
        # Check if AI wants to generate a file
        file_action = None
        if "{" in ai_response and "action" in ai_response:
            try:
                # Extract JSON from response
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    file_action = json.loads(json_str)
            except:
                pass
        
        # Save query to database
        db_query = Query(
            user_id=current_user.id,
            query_text=query.query_text,
            context=query.context
        )
        db.add(db_query)
        db.commit()
        db.refresh(db_query)
        
        # Save response to database
        db_response = Response(
            query_id=db_query.id,
            response_text=ai_response,
            model_used=llm_service.current_model
        )
        db.add(db_response)
        db.commit()
        db.refresh(db_response)
        
        response = QueryResponse(
            id=db_query.id,
            query_text=db_query.query_text,
            response_text=ai_response,
            context=query.context,
            timestamp=db_query.timestamp
        )
        
        # Add file action if found
        if file_action and file_action.get("action") == "generate_csv":
            response.file_action = file_action
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.get("/queries")
async def get_user_queries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """Get user's query history"""
    queries = db.query(Query).filter(Query.user_id == current_user.id).offset(skip).limit(limit).all()
    
    result = []
    for query in queries:
        response = db.query(Response).filter(Response.query_id == query.id).first()
        result.append({
            "id": query.id,
            "query_text": query.query_text,
            "response_text": response.response_text if response else None,
            "context": query.context,
            "timestamp": query.timestamp
        })
    
    return {"queries": result}

@app.delete("/queries/{query_id}")
async def delete_query(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user's query"""
    query = db.query(Query).filter(Query.id == query_id, Query.user_id == current_user.id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Delete associated response
    db.query(Response).filter(Response.query_id == query_id).delete()
    # Delete query
    db.delete(query)
    db.commit()
    
    return {"message": "Query deleted successfully"}

@app.get("/models")
async def get_available_models():
    """Get list of available LLM models"""
    try:
        models = await llm_service.get_available_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")

@app.post("/models/switch/{model_name}")
async def switch_model(
    model_name: str,
    current_user: User = Depends(get_current_user)
):
    """Switch to a different LLM model"""
    try:
        success = await llm_service.switch_model(model_name)
        if success:
            return {"message": f"Successfully switched to {model_name}"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to switch to {model_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error switching model: {str(e)}")

@app.post("/search/web")
async def search_web(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Search the web for information"""
    try:
        query = request.get("query", "")
        search_type = request.get("type", "general")  # general, weather
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        if search_type == "weather":
            # Extract city from query
            city = query.lower().replace("weather", "").replace("in", "").strip()
            if "poland" in city.lower():
                country = "Poland"
                city = city.replace("poland", "").strip()
            else:
                country = ""
            
            result = await web_search_service.get_weather_info(city, country)
        else:
            result = await web_search_service.search_general_info(query)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a file for processing"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the uploaded file
        file_path = os.path.join(upload_dir, f"{current_user.id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Return file info
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "file_path": file_path,
            "message": f"File {file.filename} uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.post("/files/generate-csv")
async def generate_csv(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Generate and download a CSV file based on AI request"""
    try:
        # Get data request from AI
        description = request.get("description", "")
        filename = request.get("filename", "generated_data.csv")
        
        # Generate data based on AI description
        if "europe" in description.lower() and "population" in description.lower():
            df = pd.DataFrame({
                "Country": ["Germany", "France", "Italy", "Spain", "Poland", "Ukraine", "Romania", "Netherlands", "Belgium", "Czech Republic"],
                "Population_Millions": [83.2, 67.4, 59.5, 47.4, 38.0, 41.2, 19.2, 17.4, 11.5, 10.7],
                "Capital": ["Berlin", "Paris", "Rome", "Madrid", "Warsaw", "Kyiv", "Bucharest", "Amsterdam", "Brussels", "Prague"],
                "Area_km2": [357022, 551695, 301336, 505992, 312679, 603628, 238391, 41543, 30528, 78867]
            })
        elif "sales" in description.lower():
            df = pd.DataFrame({
                "Month": ["January", "February", "March", "April", "May", "June"],
                "Sales": [15000, 18000, 22000, 19000, 25000, 28000],
                "Region": ["North", "South", "East", "West", "North", "South"],
                "Product": ["Laptop", "Phone", "Tablet", "Laptop", "Phone", "Tablet"]
            })
        elif "employee" in description.lower():
            df = pd.DataFrame({
                "Name": ["John Smith", "Jane Doe", "Mike Johnson", "Sarah Wilson", "Tom Brown"],
                "Department": ["IT", "HR", "Finance", "Marketing", "IT"],
                "Salary": [75000, 65000, 70000, 68000, 78000],
                "Years_Experience": [5, 3, 8, 4, 6]
            })
        else:
            # Default sample data
            df = pd.DataFrame({
                "ID": [1, 2, 3, 4, 5],
                "Category": ["A", "B", "A", "C", "B"],
                "Value": [100, 250, 150, 300, 200],
                "Date": pd.date_range('2024-01-01', periods=5)
            })
        
        # Create CSV content
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")

@app.post("/files/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Analyze an uploaded file"""
    try:
        content = await file.read()
        
        analysis = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "analysis": {}
        }
        
        # Analyze based on file type
        if file.content_type == "text/csv":
            # Analyze CSV file
            csv_content = content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_content))
            
            analysis["analysis"] = {
                "type": "CSV Data Analysis",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "data_types": df.dtypes.to_dict(),
                "summary": df.describe().to_dict() if len(df) > 0 else {},
                "sample_data": df.head().to_dict() if len(df) > 0 else {}
            }
        elif file.content_type.startswith("text/"):
            # Analyze text file
            text_content = content.decode('utf-8')
            words = text_content.split()
            
            analysis["analysis"] = {
                "type": "Text Analysis",
                "characters": len(text_content),
                "words": len(words),
                "lines": len(text_content.split('\n')),
                "preview": text_content[:500] + "..." if len(text_content) > 500 else text_content
            }
        else:
            analysis["analysis"] = {
                "type": "Binary File",
                "message": "File type not supported for detailed analysis"
            }
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)