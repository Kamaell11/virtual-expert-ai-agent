from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any

# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Query Schemas
class QueryBase(BaseModel):
    query_text: str
    context: Optional[str] = None

class QueryCreate(QueryBase):
    pass

class QueryResponse(QueryBase):
    id: int
    response_text: str
    timestamp: datetime
    model_used: Optional[str] = None
    file_action: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Response Schemas
class ResponseBase(BaseModel):
    response_text: str
    model_used: Optional[str] = None
    processing_time: Optional[int] = None

class ResponseCreate(ResponseBase):
    query_id: int

class ResponseInDB(ResponseBase):
    id: int
    query_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Agent Schemas
class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_name: str
    parameters: Optional[str] = None

class AgentCreate(AgentBase):
    pass

class AgentResponse(AgentBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Chat Schemas
class ChatMessage(BaseModel):
    message: str
    timestamp: datetime
    is_user: bool

class ChatSession(BaseModel):
    id: str
    messages: List[ChatMessage]
    created_at: datetime

# System Schemas
class HealthCheck(BaseModel):
    status: str
    services: dict
    timestamp: datetime

class ModelInfo(BaseModel):
    name: str
    size: Optional[str] = None
    description: Optional[str] = None
    available: bool = True

# Fine-Tuned Model Schemas
class FineTunedModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_model: str
    specialization: Optional[str] = None

class FineTunedModelCreate(FineTunedModelBase):
    pass

class FineTunedModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    specialization: Optional[str] = None

class FineTunedModelResponse(FineTunedModelBase):
    id: int
    model_path: str
    model_size: Optional[int] = None
    training_status: str
    training_progress: int
    accuracy_score: Optional[str] = None
    loss_score: Optional[str] = None
    is_active: bool
    owner_id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Training Dataset Schemas
class TrainingDatasetBase(BaseModel):
    filename: str
    dataset_type: str

class TrainingDatasetCreate(TrainingDatasetBase):
    model_id: int
    file_path: str
    file_size: Optional[int] = None

class TrainingDatasetResponse(TrainingDatasetBase):
    id: int
    model_id: int
    file_path: str
    file_size: Optional[int] = None
    validation_status: str
    validation_errors: Optional[str] = None
    row_count: Optional[int] = None
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True

# Fine-Tuning Log Schemas
class FineTuningLogResponse(BaseModel):
    id: int
    model_id: int
    log_level: str
    message: str
    step: Optional[int] = None
    epoch: Optional[int] = None
    loss: Optional[str] = None
    accuracy: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Fine-Tuning Request Schemas
class FineTuningRequest(BaseModel):
    model_name: str
    base_model: str
    specialization: str
    description: Optional[str] = None
    training_params: Optional[Dict[str, Any]] = None

class DatasetUploadRequest(BaseModel):
    dataset_type: str
    description: Optional[str] = None

class DatasetValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    row_count: Optional[int] = None
    column_info: Optional[Dict[str, Any]] = None

# User Model Access Schemas
class UserModelAccessBase(BaseModel):
    user_id: int
    model_id: int
    access_level: str = 'read'

class UserModelAccessCreate(UserModelAccessBase):
    expires_at: Optional[datetime] = None

class UserModelAccessResponse(UserModelAccessBase):
    id: int
    granted_by: int
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True