from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """User model for authentication and user management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    fine_tuned_models = relationship("FineTunedModel", back_populates="owner", cascade="all, delete-orphan")

class Query(Base):
    """Query model for storing user queries"""
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="queries")
    responses = relationship("Response", back_populates="query", cascade="all, delete-orphan")

class Response(Base):
    """Response model for storing AI-generated responses"""
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=True)
    processing_time = Column(Integer, nullable=True)  # in milliseconds
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    query = relationship("Query", back_populates="responses")

class Agent(Base):
    """Agent model for different AI agent configurations"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False)
    parameters = Column(Text, nullable=True)  # JSON string for model parameters
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User")

class FineTunedModel(Base):
    """Fine-tuned model storage per client"""
    __tablename__ = "fine_tuned_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    base_model = Column(String(100), nullable=False)  # Base model used for fine-tuning
    model_path = Column(String(255), nullable=False)  # Path to fine-tuned model files
    model_size = Column(Integer, nullable=True)  # Size in bytes
    specialization = Column(String(100), nullable=True)  # Domain (e.g., 'lawyer', 'doctor', 'mechanic')
    training_status = Column(String(50), default='pending')  # pending, training, completed, failed
    training_progress = Column(Integer, default=0)  # Progress percentage
    accuracy_score = Column(String(50), nullable=True)  # Training accuracy metrics
    loss_score = Column(String(50), nullable=True)  # Training loss metrics
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="fine_tuned_models")
    training_datasets = relationship("TrainingDataset", back_populates="model", cascade="all, delete-orphan")
    training_logs = relationship("FineTuningLog", back_populates="model", cascade="all, delete-orphan")

class TrainingDataset(Base):
    """Training datasets for fine-tuning"""
    __tablename__ = "training_datasets"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("fine_tuned_models.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    dataset_type = Column(String(50), nullable=False)  # 'jsonl', 'csv', 'txt'
    validation_status = Column(String(50), default='pending')  # pending, valid, invalid
    validation_errors = Column(Text, nullable=True)
    row_count = Column(Integer, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    model = relationship("FineTunedModel", back_populates="training_datasets")
    uploader = relationship("User")

class FineTuningLog(Base):
    """Logs for fine-tuning process"""
    __tablename__ = "fine_tuning_logs"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("fine_tuned_models.id"), nullable=False)
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    step = Column(Integer, nullable=True)  # Training step
    epoch = Column(Integer, nullable=True)  # Training epoch
    loss = Column(String(50), nullable=True)  # Current loss value
    accuracy = Column(String(50), nullable=True)  # Current accuracy
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    model = relationship("FineTunedModel", back_populates="training_logs")

class UserModelAccess(Base):
    """User access permissions to fine-tuned models"""
    __tablename__ = "user_model_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("fine_tuned_models.id"), nullable=False)
    access_level = Column(String(20), default='read')  # read, write, admin
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    model = relationship("FineTunedModel")
    granter = relationship("User", foreign_keys=[granted_by])