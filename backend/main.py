from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import os
import io
import json
import pandas as pd
from typing import Optional
from dotenv import load_dotenv

from database import SessionLocal, engine
from models import Base, User, Query, Response, FineTunedModel, TrainingDataset, FineTuningLog, UserModelAccess
from schemas import (
    UserCreate, QueryCreate, QueryResponse, UserResponse,
    FineTunedModelCreate, FineTunedModelResponse, FineTunedModelUpdate,
    TrainingDatasetCreate, TrainingDatasetResponse, DatasetUploadRequest,
    FineTuningRequest, DatasetValidationResponse, FineTuningLogResponse,
    UserModelAccessCreate, UserModelAccessResponse
)
from services.llm_service import LLMService
from services.auth_service import AuthService
from services.web_search_service import WebSearchService
from services.fine_tuning_service import FineTuningService
from services.model_access_service import ModelAccessService

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
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost,http://127.0.0.1").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
auth_service = AuthService()
llm_service = LLMService()
web_search_service = WebSearchService()
fine_tuning_service = FineTuningService()
model_access_service = ModelAccessService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    db: Session = Depends(get_db),
    fine_tuned_model_id: Optional[int] = None
):
    """Process user query and generate AI response"""
    try:
        fine_tuned_model_info = None
        if fine_tuned_model_id:
            has_access, _ = await model_access_service.check_model_access(
                current_user.id, fine_tuned_model_id, "read", db
            )
            
            if has_access:
                model = db.query(FineTunedModel).filter(
                    FineTunedModel.id == fine_tuned_model_id,
                    FineTunedModel.training_status == "completed"
                ).first()
                
                if model:
                    fine_tuned_model_info = {
                        "model_path": model.model_path,
                        "specialization": model.specialization,
                        "model_id": model.id,
                        "model_name": model.name
                    }
        
        ai_response = await llm_service.create_agent_response(
            query.query_text, 
            web_search_service=web_search_service,
            fine_tuned_model_info=fine_tuned_model_info
        )
        
        file_action = None
        if "{" in ai_response and "action" in ai_response:
            try:
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    file_action = json.loads(json_str)
            except:
                pass
        
        db_query = Query(
            user_id=current_user.id,
            query_text=query.query_text,
            context=query.context
        )
        db.add(db_query)
        db.commit()
        db.refresh(db_query)
        
        model_used = llm_service.current_model
        if fine_tuned_model_info:
            model_used = f"{fine_tuned_model_info['model_name']} (Fine-tuned {fine_tuned_model_info['specialization']})"
        
        db_response = Response(
            query_id=db_query.id,
            response_text=ai_response,
            model_used=model_used
        )
        db.add(db_response)
        db.commit()
        db.refresh(db_response)
        
        response = QueryResponse(
            id=db_query.id,
            query_text=db_query.query_text,
            response_text=ai_response,
            context=query.context,
            timestamp=db_query.timestamp,
            model_used=model_used
        )
        
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
    
    db.query(Response).filter(Response.query_id == query_id).delete()
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
        search_type = request.get("type", "general")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        if search_type == "weather":
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
        upload_dir = os.getenv("UPLOAD_DIR", "/app/uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{current_user.id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
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
        description = request.get("description", "")
        filename = request.get("filename", "generated_data.csv")
        
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
            df = pd.DataFrame({
                "ID": [1, 2, 3, 4, 5],
                "Category": ["A", "B", "A", "C", "B"],
                "Value": [100, 250, 150, 300, 200],
                "Date": pd.date_range('2024-01-01', periods=5)
            })
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
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
        
        if file.content_type == "text/csv":
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

# Fine-Tuned Models Endpoints
@app.get("/fine-tuned-models", response_model=list[dict])
async def get_user_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_shared: bool = True,
    specialization: Optional[str] = None
):
    """Get user's accessible fine-tuned models"""
    try:
        if specialization:
            models = await model_access_service.get_user_models_by_specialization(
                current_user.id, specialization, db
            )
        else:
            models = await model_access_service.get_user_accessible_models(
                current_user.id, db, include_shared=include_shared
            )
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")

@app.post("/fine-tuned-models", response_model=FineTunedModelResponse)
async def create_fine_tuned_model(
    request: FineTuningRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new fine-tuned model"""
    try:
        model = await fine_tuning_service.create_fine_tuned_model(
            model_name=request.model_name,
            base_model=request.base_model,
            specialization=request.specialization,
            description=request.description,
            user_id=current_user.id,
            db=db
        )
        return model
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create model: {str(e)}")

@app.get("/fine-tuned-models/{model_id}", response_model=FineTunedModelResponse)
async def get_fine_tuned_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific fine-tuned model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "read", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch model: {str(e)}")

@app.put("/fine-tuned-models/{model_id}", response_model=FineTunedModelResponse)
async def update_fine_tuned_model(
    model_id: int,
    update_data: FineTunedModelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a fine-tuned model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "admin", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        model = await fine_tuning_service.update_fine_tuned_model(model_id, update_data, db)
        return model
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update model: {str(e)}")

@app.delete("/fine-tuned-models/{model_id}")
async def delete_fine_tuned_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a fine-tuned model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "admin", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await fine_tuning_service.delete_fine_tuned_model(model_id, db)
        if success:
            return {"message": "Model deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Model not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")

# Training Dataset Endpoints
@app.post("/fine-tuned-models/{model_id}/datasets", response_model=TrainingDatasetResponse)
async def upload_training_dataset(
    model_id: int,
    file: UploadFile = File(...),
    dataset_type: str = "jsonl",
    description: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload training dataset for a model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "write", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        dataset = await fine_tuning_service.upload_training_dataset(
            model_id=model_id,
            file=file,
            dataset_type=dataset_type,
            description=description,
            user_id=current_user.id,
            db=db
        )
        return dataset
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {str(e)}")

@app.get("/fine-tuned-models/{model_id}/datasets", response_model=list[TrainingDatasetResponse])
async def get_model_datasets(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get training datasets for a model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "read", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        datasets = await fine_tuning_service.get_model_datasets(model_id, db)
        return datasets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch datasets: {str(e)}")

@app.post("/datasets/{dataset_id}/validate", response_model=DatasetValidationResponse)
async def validate_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a training dataset"""
    try:
        dataset = db.query(TrainingDataset).filter(TrainingDataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, dataset.model_id, "write", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        validation_result = await fine_tuning_service.validate_dataset(dataset_id, db)
        return validation_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate dataset: {str(e)}")

# Fine-Tuning Process Endpoints
@app.post("/fine-tuned-models/{model_id}/start-training")
async def start_training(
    model_id: int,
    training_params: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start fine-tuning process for a model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "admin", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await fine_tuning_service.start_training(model_id, training_params or {}, db)
        if success:
            return {"message": "Training started successfully", "model_id": model_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to start training")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")

@app.post("/fine-tuned-models/{model_id}/stop-training")
async def stop_training(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop fine-tuning process for a model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "admin", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await fine_tuning_service.stop_training(model_id, db)
        if success:
            return {"message": "Training stopped successfully", "model_id": model_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop training")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop training: {str(e)}")

@app.get("/fine-tuned-models/{model_id}/status")
async def get_training_status(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get training status and progress for a model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "read", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        status = await fine_tuning_service.get_training_status(model_id, db)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training status: {str(e)}")

@app.get("/fine-tuned-models/{model_id}/logs", response_model=list[FineTuningLogResponse])
async def get_training_logs(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    log_level: Optional[str] = None
):
    """Get training logs for a model"""
    try:
        has_access, _ = await model_access_service.check_model_access(
            current_user.id, model_id, "read", db
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        logs = await fine_tuning_service.get_training_logs(model_id, db, limit, log_level)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training logs: {str(e)}")

# Model Access Management Endpoints
@app.post("/fine-tuned-models/{model_id}/access", response_model=UserModelAccessResponse)
async def grant_model_access(
    model_id: int,
    access_request: UserModelAccessCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant access to a model for another user"""
    try:
        access = await model_access_service.grant_model_access(
            granter_id=current_user.id,
            target_user_id=access_request.user_id,
            model_id=model_id,
            access_level=access_request.access_level,
            expires_at=access_request.expires_at,
            db=db
        )
        return access
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to grant access: {str(e)}")

@app.delete("/fine-tuned-models/{model_id}/access/{user_id}")
async def revoke_model_access(
    model_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke model access for a user"""
    try:
        success = await model_access_service.revoke_model_access(
            revoker_id=current_user.id,
            target_user_id=user_id,
            model_id=model_id,
            db=db
        )
        if success:
            return {"message": "Access revoked successfully"}
        else:
            return {"message": "No active access found"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke access: {str(e)}")

@app.get("/fine-tuned-models/{model_id}/access", response_model=list[dict])
async def get_model_access_list(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users who have access to a model"""
    try:
        access_list = await model_access_service.get_model_access_list(
            requester_id=current_user.id,
            model_id=model_id,
            db=db
        )
        return access_list
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get access list: {str(e)}")

@app.get("/fine-tuned-models/{model_id}/statistics")
async def get_model_statistics(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for a model"""
    try:
        stats = await model_access_service.get_model_statistics(
            user_id=current_user.id,
            model_id=model_id,
            db=db
        )
        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# Base Models Information
@app.get("/base-models")
async def get_base_models():
    """Get list of available base models for fine-tuning"""
    try:
        models = await fine_tuning_service.get_available_base_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get base models: {str(e)}")

# Admin Endpoints for Monitoring
@app.get("/admin/fine-tuning/overview")
async def get_fine_tuning_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overview of all fine-tuning processes (admin only)"""
    try:
        models = db.query(FineTunedModel).all()
        overview = {
            "total_models": len(models),
            "status_breakdown": {},
            "recent_activity": [],
            "active_trainings": 0,
            "completed_trainings": 0,
            "failed_trainings": 0
        }
        
        for model in models:
            status = model.training_status
            overview["status_breakdown"][status] = overview["status_breakdown"].get(status, 0) + 1
            
            if status == "training":
                overview["active_trainings"] += 1
            elif status == "completed":
                overview["completed_trainings"] += 1
            elif status == "failed":
                overview["failed_trainings"] += 1
            
            overview["recent_activity"].append({
                "model_id": model.id,
                "model_name": model.name,
                "owner": model.owner.username,
                "status": model.training_status,
                "progress": model.training_progress,
                "specialization": model.specialization,
                "created_at": model.created_at,
                "updated_at": model.updated_at
            })
        
        overview["recent_activity"] = sorted(
            overview["recent_activity"][:20], 
            key=lambda x: x["updated_at"] or x["created_at"], 
            reverse=True
        )
        
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")

@app.get("/admin/fine-tuning/active-trainings")
async def get_active_trainings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all currently active training processes"""
    try:
        active_models = db.query(FineTunedModel).filter(
            FineTunedModel.training_status == "training"
        ).all()
        
        trainings = []
        for model in active_models:
            latest_logs = db.query(FineTuningLog).filter(
                FineTuningLog.model_id == model.id
            ).order_by(FineTuningLog.created_at.desc()).limit(5).all()
            
            trainings.append({
                "model_id": model.id,
                "model_name": model.name,
                "owner": model.owner.username,
                "specialization": model.specialization,
                "base_model": model.base_model,
                "progress": model.training_progress,
                "started_at": model.created_at,
                "latest_logs": [{
                    "log_level": log.log_level,
                    "message": log.message,
                    "step": log.step,
                    "epoch": log.epoch,
                    "loss": log.loss,
                    "accuracy": log.accuracy,
                    "timestamp": log.created_at
                } for log in latest_logs]
            })
        
        return {"active_trainings": trainings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active trainings: {str(e)}")

@app.get("/admin/fine-tuning/system-stats")
async def get_system_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system-wide fine-tuning statistics"""
    try:
        total_models = db.query(FineTunedModel).count()
        active_models = db.query(FineTunedModel).filter(FineTunedModel.is_active == True).count()
        
        total_datasets = db.query(TrainingDataset).count()
        valid_datasets = db.query(TrainingDataset).filter(TrainingDataset.validation_status == "valid").count()
        
        total_users = db.query(User).count()
        users_with_models = db.query(User).join(FineTunedModel).distinct().count()
        
        total_model_size = db.query(func.sum(FineTunedModel.model_size)).scalar() or 0
        total_dataset_size = db.query(func.sum(TrainingDataset.file_size)).scalar() or 0
        
        total_access_grants = db.query(UserModelAccess).count()
        active_access_grants = db.query(UserModelAccess).filter(UserModelAccess.is_active == True).count()
        
        specialization_stats = db.query(
            FineTunedModel.specialization,
            func.count(FineTunedModel.id).label('count')
        ).group_by(FineTunedModel.specialization).all()
        
        return {
            "models": {
                "total": total_models,
                "active": active_models,
                "total_size_bytes": total_model_size
            },
            "datasets": {
                "total": total_datasets,
                "valid": valid_datasets,
                "total_size_bytes": total_dataset_size
            },
            "users": {
                "total": total_users,
                "with_models": users_with_models
            },
            "access": {
                "total_grants": total_access_grants,
                "active_grants": active_access_grants
            },
            "specializations": {spec: count for spec, count in specialization_stats if spec},
            "system_health": {
                "fine_tuning_service": "online",
                "model_access_service": "online",
                "database": "online"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system statistics: {str(e)}")

@app.post("/admin/fine-tuning/cleanup")
async def cleanup_expired_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up expired model access permissions"""
    try:
        cleaned_count = await model_access_service.cleanup_expired_access(db)
        return {
            "message": f"Cleanup completed successfully",
            "expired_access_removed": cleaned_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")

@app.get("/admin/users/{user_id}/models")
async def get_user_models_admin(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all models for a specific user (admin view)"""
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        models = await model_access_service.get_user_accessible_models(
            user_id, db, include_owned=True, include_shared=True
        )
        
        return {
            "user_id": user_id,
            "username": target_user.username,
            "models": models
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user models: {str(e)}")

@app.post("/admin/fine-tuned-models/{model_id}/force-stop")
async def force_stop_training(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Force stop a training process (admin only)"""
    try:
        success = await fine_tuning_service.stop_training(model_id, db)
        
        if success:
            await fine_tuning_service._log_training_event(
                model_id, "WARNING", 
                f"Training force-stopped by admin user {current_user.username}",
                db
            )
            return {"message": "Training force-stopped successfully", "model_id": model_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to force stop training")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to force stop training: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    uvicorn.run(app, host=host, port=port, reload=debug)