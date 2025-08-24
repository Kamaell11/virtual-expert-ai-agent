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