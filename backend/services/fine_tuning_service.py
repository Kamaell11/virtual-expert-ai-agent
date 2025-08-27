import os
import json
import asyncio
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
import logging
from concurrent.futures import ThreadPoolExecutor

from models import FineTunedModel, TrainingDataset, FineTuningLog, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FineTuningService:
    """Service for managing fine-tuned models (simulation)"""
    
    def __init__(self):
        self.models_dir = os.getenv("FINE_TUNED_MODELS_DIR", "/app/models/fine_tuned")
        self.datasets_dir = os.getenv("TRAINING_DATASETS_DIR", "/app/datasets")
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.active_trainings = {}
        
        # Available base models for fine-tuning
        self.available_base_models = {
            "microsoft/DialoGPT-medium": {
                "name": "DialoGPT Medium",
                "description": "Conversational AI model",
                "specializations": ["customer_service", "general_chat", "medical", "legal", "mechanic"]
            },
            "microsoft/DialoGPT-small": {
                "name": "DialoGPT Small", 
                "description": "Lightweight conversational AI",
                "specializations": ["customer_service", "general_chat"]
            },
            "distilgpt2": {
                "name": "DistilGPT-2",
                "description": "Efficient text generation model",
                "specializations": ["medical", "legal", "mechanic", "general_chat"]
            }
        }
        
        # Create directories if they don't exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.datasets_dir, exist_ok=True)
    
    async def get_available_base_models(self) -> Dict[str, Any]:
        """Get available base models for fine-tuning"""
        return self.available_base_models
    
    async def create_fine_tuned_model(
        self,
        model_name: str,
        base_model: str,
        specialization: str,
        description: Optional[str],
        user_id: int,
        db: Session
    ) -> FineTunedModel:
        """Create a new fine-tuned model entry"""
        
        if base_model not in self.available_base_models:
            raise ValueError(f"Base model {base_model} is not supported")
        
        # Check if specialization is supported for this base model
        supported_specs = self.available_base_models[base_model]["specializations"]
        if specialization not in supported_specs:
            raise ValueError(f"Specialization {specialization} not supported for {base_model}")
        
        # Create unique model path
        model_path = os.path.join(self.models_dir, f"{user_id}_{model_name}_{int(datetime.now().timestamp())}")
        
        model = FineTunedModel(
            name=model_name,
            description=description,
            base_model=base_model,
            model_path=model_path,
            specialization=specialization,
            training_status="pending",
            training_progress=0,
            owner_id=user_id
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        # Create default dataset for specialization if available
        await self._create_default_dataset(model, specialization, user_id, db)
        
        logger.info(f"Created fine-tuned model: {model_name} for user {user_id}")
        return model
    
    async def upload_training_dataset(
        self,
        model_id: int,
        file: Any,  # UploadFile
        dataset_type: str,
        description: Optional[str],
        user_id: int,
        db: Session
    ) -> TrainingDataset:
        """Upload and validate training dataset"""
        
        # Create unique filename
        timestamp = int(datetime.now().timestamp())
        filename = f"{user_id}_{model_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(self.datasets_dir, filename)
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Create dataset entry
        dataset = TrainingDataset(
            model_id=model_id,
            filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            dataset_type=dataset_type,
            validation_status="pending",
            uploaded_by=user_id
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # Validate dataset asynchronously
        await self.validate_dataset(dataset.id, db)
        
        return dataset
    
    async def validate_dataset(self, dataset_id: int, db: Session) -> Dict[str, Any]:
        """Validate training dataset format"""
        
        dataset = db.query(TrainingDataset).filter(TrainingDataset.id == dataset_id).first()
        if not dataset:
            raise ValueError("Dataset not found")
        
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "row_count": 0,
            "column_info": {}
        }
        
        try:
            # Validate based on file type
            if dataset.dataset_type.lower() == "jsonl":
                validation_result = await self._validate_jsonl(dataset.file_path)
            elif dataset.dataset_type.lower() == "csv":
                validation_result = await self._validate_csv(dataset.file_path)
            elif dataset.dataset_type.lower() == "pdf":
                validation_result = await self._validate_pdf(dataset.file_path)
            elif dataset.dataset_type.lower() == "txt":
                validation_result = await self._validate_txt(dataset.file_path)
            else:
                validation_result["errors"].append(f"Unsupported dataset type: {dataset.dataset_type}")
            
            # Update dataset validation status
            if validation_result["is_valid"]:
                dataset.validation_status = "valid"
                dataset.row_count = validation_result["row_count"]
                dataset.validation_errors = None
            else:
                dataset.validation_status = "invalid"
                dataset.validation_errors = json.dumps(validation_result["errors"])
            
            db.commit()
            
            await self._log_training_event(
                dataset.model_id, "INFO",
                f"Dataset validation completed: {len(validation_result['errors'])} errors found",
                db
            )
            
        except Exception as e:
            dataset.validation_status = "invalid"
            dataset.validation_errors = str(e)
            db.commit()
            
            await self._log_training_event(
                dataset.model_id, "ERROR",
                f"Dataset validation failed: {str(e)}",
                db
            )
            
            validation_result["errors"].append(str(e))
        
        return validation_result
    
    async def _validate_jsonl(self, file_path: str) -> Dict[str, Any]:
        """Validate JSONL format"""
        errors = []
        warnings = []
        row_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        row_count += 1
                        
                        # Check required fields for fine-tuning
                        if not isinstance(data, dict):
                            errors.append(f"Line {line_num}: Expected object, got {type(data).__name__}")
                            continue
                        
                        # Check for instruction-based format
                        if "instruction" in data and "output" in data:
                            # Valid instruction format
                            pass
                        elif "input" in data and "output" in data:
                            # Valid input-output format
                            pass
                        else:
                            warnings.append(f"Line {line_num}: Missing expected fields (instruction/input + output)")
                        
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "row_count": row_count,
                "column_info": {"format": "jsonl", "fields": ["instruction/input", "output"]}
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"File reading error: {str(e)}"],
                "warnings": [],
                "row_count": 0,
                "column_info": {}
            }
    
    async def _validate_csv(self, file_path: str) -> Dict[str, Any]:
        """Validate CSV format"""
        errors = []
        warnings = []
        
        try:
            df = pd.read_csv(file_path)
            row_count = len(df)
            
            # Check required columns
            required_columns = ["input", "output"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                errors.append(f"Missing required columns: {missing_columns}")
            
            # Check for empty rows
            empty_rows = df.isnull().all(axis=1).sum()
            if empty_rows > 0:
                warnings.append(f"{empty_rows} empty rows found")
            
            # Check column info
            column_info = {
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict()
            }
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "row_count": row_count,
                "column_info": column_info
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"CSV reading error: {str(e)}"],
                "warnings": [],
                "row_count": 0,
                "column_info": {}
            }
    
    async def get_model_datasets(self, model_id: int, db: Session) -> List[TrainingDataset]:
        """Get all datasets for a model"""
        datasets = db.query(TrainingDataset).filter(
            TrainingDataset.model_id == model_id
        ).all()
        return datasets
    
    async def start_training(
        self,
        model_id: int,
        training_params: Dict,
        db: Session
    ) -> bool:
        """Start fine-tuning process"""
        
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        if not model:
            return False
        
        # Check if already training
        if model.training_status == "training":
            return False
        
        # Get valid datasets
        datasets = db.query(TrainingDataset).filter(
            TrainingDataset.model_id == model_id,
            TrainingDataset.validation_status == "valid"
        ).all()
        
        if not datasets:
            raise ValueError("No valid datasets found for training")
        
        # Start training asynchronously
        model.training_status = "training"
        model.training_progress = 0
        db.commit()
        
        # Submit training task to executor
        future = self.executor.submit(
            asyncio.run, 
            self._train_with_simulation(model, datasets, training_params, db)
        )
        self.active_trainings[model_id] = future
        
        return True
    
    async def _train_with_simulation(
        self,
        model: FineTunedModel,
        datasets: List[TrainingDataset],
        training_params: Dict,
        db: Session
    ):
        """Simulate training process"""
        try:
            await self._log_training_event(
                model.id, "INFO", "Starting simulated fine-tuning process", db
            )
            
            # Simulate training progress
            total_steps = training_params.get("max_steps", 50)
            
            for step in range(0, total_steps + 1, 2):
                if not self._should_continue_training(model.id, db):
                    break
                
                # Calculate progress
                progress = min(100, int((step / total_steps) * 100))
                
                # Update model progress in database
                db.query(FineTunedModel).filter(FineTunedModel.id == model.id).update({
                    "training_progress": progress
                })
                db.commit()
                
                # Simulate training metrics
                loss = max(0.1, 2.0 - (step / total_steps) * 1.8)
                accuracy = min(0.95, 0.5 + (step / total_steps) * 0.45)
                
                # Log progress with metrics
                await self._log_training_event(
                    model.id, "INFO", 
                    f"Training progress: {progress}% (Step {step}/{total_steps})",
                    db, step=step, loss=f"{loss:.4f}", accuracy=f"{accuracy:.4f}"
                )
                
                # Simulate training time
                await asyncio.sleep(1)
            
            # Mark as completed
            db.query(FineTunedModel).filter(FineTunedModel.id == model.id).update({
                "training_status": "completed",
                "training_progress": 100,
                "completed_at": datetime.now(timezone.utc),
                "model_size": 10 * 1024 * 1024  # 10MB simulated
            })
            db.commit()
            
            await self._log_training_event(
                model.id, "INFO", "Fine-tuning completed successfully!", db
            )
            
        except Exception as e:
            db.query(FineTunedModel).filter(FineTunedModel.id == model.id).update({
                "training_status": "failed"
            })
            db.commit()
            
            await self._log_training_event(
                model.id, "ERROR", f"Training failed: {str(e)}", db
            )
        finally:
            # Remove from active trainings
            if model.id in self.active_trainings:
                del self.active_trainings[model.id]
    
    def _should_continue_training(self, model_id: int, db: Session) -> bool:
        """Check if training should continue"""
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        return model and model.training_status == "training"
    
    async def stop_training(self, model_id: int, db: Session) -> bool:
        """Stop training process"""
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        if not model or model.training_status != "training":
            return False
        
        model.training_status = "stopped"
        db.commit()
        
        await self._log_training_event(
            model.id, "WARNING", "Training stopped by user", db
        )
        
        return True
    
    async def get_training_status(self, model_id: int, db: Session) -> Dict[str, Any]:
        """Get current training status"""
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        if not model:
            raise ValueError("Model not found")
        
        return {
            "model_id": model_id,
            "status": model.training_status,
            "progress": model.training_progress,
            "created_at": model.created_at,
            "completed_at": model.completed_at,
            "model_size": model.model_size
        }
    
    async def get_training_logs(
        self,
        model_id: int,
        db: Session,
        limit: int = 100,
        log_level: Optional[str] = None
    ) -> List[FineTuningLog]:
        """Get training logs for a model"""
        
        query = db.query(FineTuningLog).filter(FineTuningLog.model_id == model_id)
        
        if log_level:
            query = query.filter(FineTuningLog.log_level == log_level.upper())
        
        logs = query.order_by(FineTuningLog.created_at.desc()).limit(limit).all()
        return logs
    
    async def _log_training_event(
        self,
        model_id: int,
        level: str,
        message: str,
        db: Session,
        step: Optional[int] = None,
        epoch: Optional[int] = None,
        loss: Optional[str] = None,
        accuracy: Optional[str] = None
    ):
        """Log training event"""
        
        log_entry = FineTuningLog(
            model_id=model_id,
            log_level=level,
            message=message,
            step=step,
            epoch=epoch,
            loss=loss,
            accuracy=accuracy
        )
        
        db.add(log_entry)
        db.commit()
        
        logger.info(f"Model {model_id}: {level} - {message}")
    
    async def update_fine_tuned_model(
        self,
        model_id: int,
        update_data: Any,  # FineTunedModelUpdate
        db: Session
    ) -> FineTunedModel:
        """Update fine-tuned model"""
        
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        if not model:
            raise ValueError("Model not found")
        
        # Update fields
        if hasattr(update_data, 'name') and update_data.name is not None:
            model.name = update_data.name
        if hasattr(update_data, 'description') and update_data.description is not None:
            model.description = update_data.description
        if hasattr(update_data, 'is_active') and update_data.is_active is not None:
            model.is_active = update_data.is_active
        if hasattr(update_data, 'specialization') and update_data.specialization is not None:
            model.specialization = update_data.specialization
        
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(model)
        
        return model
    
    async def delete_fine_tuned_model(self, model_id: int, db: Session) -> bool:
        """Delete fine-tuned model"""
        
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        if not model:
            return False
        
        # Stop training if active
        if model.training_status == "training":
            await self.stop_training(model_id, db)
        
        # Delete model files if they exist
        if os.path.exists(model.model_path):
            import shutil
            shutil.rmtree(model.model_path, ignore_errors=True)
        
        # Delete from database (cascade will handle related records)
        db.delete(model)
        db.commit()
        
        return True
    
    async def _validate_pdf(self, file_path: str) -> Dict[str, Any]:
        """Validate PDF format (basic check)"""
        errors = []
        warnings = []
        
        try:
            # Check if file exists and has content
            if not os.path.exists(file_path):
                errors.append("File not found")
                return {
                    "is_valid": False,
                    "errors": errors,
                    "warnings": warnings,
                    "row_count": 0,
                    "column_info": {"format": "pdf", "note": "PDF files are accepted but may need manual preprocessing"}
                }
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                errors.append("File is empty")
            elif file_size > 50 * 1024 * 1024:  # 50MB limit
                warnings.append("Large PDF file - may take longer to process")
            
            # For now, accept any PDF as valid but with warnings
            warnings.append("PDF files require manual preprocessing into structured training data")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "row_count": 1,  # PDF treated as single document
                "column_info": {"format": "pdf", "note": "PDF content will be extracted during training"}
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"PDF validation error: {str(e)}"],
                "warnings": [],
                "row_count": 0,
                "column_info": {}
            }
    
    async def _validate_txt(self, file_path: str) -> Dict[str, Any]:
        """Validate TXT format"""
        errors = []
        warnings = []
        
        try:
            if not os.path.exists(file_path):
                errors.append("File not found")
                return {
                    "is_valid": False,
                    "errors": errors,
                    "warnings": warnings,
                    "row_count": 0,
                    "column_info": {}
                }
            
            line_count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():  # Count non-empty lines
                        line_count += 1
            
            if line_count == 0:
                errors.append("File is empty or contains no text")
            
            # TXT files are treated as free-form text data
            warnings.append("TXT files will be processed as free-form text - consider converting to JSONL for better training results")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "row_count": line_count,
                "column_info": {"format": "txt", "lines": line_count}
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"TXT validation error: {str(e)}"],
                "warnings": [],
                "row_count": 0,
                "column_info": {}
            }
    
    async def _create_default_dataset(self, model: FineTunedModel, specialization: str, user_id: int, db: Session):
        """Create default dataset for specialization"""
        
        # Default training data for different specializations
        default_datasets = {
            "medical": [
                {"instruction": "What are the symptoms of diabetes?", "output": "Common symptoms of diabetes include increased thirst, frequent urination, fatigue, blurred vision, slow healing wounds, and unexplained weight loss. If you experience these symptoms, consult a healthcare professional."},
                {"instruction": "How is high blood pressure treated?", "output": "High blood pressure is typically treated with lifestyle changes like diet modification, exercise, and stress management. Medications may include ACE inhibitors, diuretics, or beta-blockers. Always follow your doctor's treatment plan."},
                {"instruction": "What should I do for a fever?", "output": "For fever, rest, stay hydrated, and consider over-the-counter fever reducers like acetaminophen or ibuprofen. Seek medical attention if fever exceeds 103°F (39.4°C) or persists for more than 3 days."},
                {"instruction": "What are the signs of a heart attack?", "output": "Warning signs include chest pain or pressure, shortness of breath, nausea, sweating, and pain in arms, neck, jaw, or back. This is a medical emergency - call 911 immediately if you suspect a heart attack."},
            ],
            "legal": [
                {"instruction": "What should I do if I'm in a car accident?", "output": "After ensuring safety: call police, exchange insurance information, document the scene with photos, get witness contacts, and notify your insurance company. Avoid admitting fault. Consider consulting a lawyer for significant damages."},
                {"instruction": "How do I write a valid will?", "output": "A valid will typically requires: being of sound mind, signing in the presence of witnesses, clear identification of beneficiaries and assets. Requirements vary by jurisdiction. Consult an attorney to ensure legal compliance."},
                {"instruction": "What are my rights during a police stop?", "output": "You have the right to remain silent, the right to refuse searches (in most cases), and the right to an attorney. Be polite and comply with lawful orders. You can ask if you're free to leave."},
                {"instruction": "How do I handle a contract dispute?", "output": "Review the contract terms, gather relevant documentation, attempt good-faith negotiation, and consider mediation. If unsuccessful, consult a contract attorney to understand your legal options and potential remedies."},
            ],
            "mechanic": [
                {"instruction": "Why is my car engine overheating?", "output": "Common causes include low coolant, broken thermostat, damaged radiator, failed water pump, or blocked cooling system. Stop driving immediately, let engine cool, check coolant level, and consult a mechanic if problem persists."},
                {"instruction": "What causes a car to not start?", "output": "Common issues: dead battery, faulty starter, fuel system problems, ignition issues, or security system activation. Check battery connections, listen for starter sounds, and verify fuel gauge. May require professional diagnosis."},
                {"instruction": "How often should I change my oil?", "output": "Typically every 3,000-7,500 miles depending on oil type and driving conditions. Conventional oil: 3,000-5,000 miles. Synthetic oil: 7,500-10,000 miles. Check owner's manual for manufacturer recommendations."},
                {"instruction": "What does it mean when my check engine light comes on?", "output": "Check engine light indicates a potential emissions or engine problem detected by the vehicle's computer. Use an OBD-II scanner to read error codes, or visit an auto parts store for free scanning. Address promptly to prevent damage."},
            ],
            "general_chat": [
                {"instruction": "How are you today?", "output": "I'm doing well, thank you for asking! I'm here and ready to help you with any questions or tasks you might have. How are you doing today?"},
                {"instruction": "What's the weather like?", "output": "I don't have access to real-time weather data, but I'd be happy to help you find weather information! You can check weather apps, websites like weather.com, or ask a voice assistant for current conditions in your area."},
                {"instruction": "Tell me a joke", "output": "Here's a light-hearted one: Why don't scientists trust atoms? Because they make up everything! I hope that brought a smile to your face. Would you like to hear another one?"},
                {"instruction": "What can you help me with?", "output": "I can help with a wide variety of tasks including answering questions, providing information, helping with analysis, creative writing, problem-solving, and general conversation. What would you like assistance with today?"},
            ]
        }
        
        if specialization not in default_datasets:
            return  # No default dataset available
        
        try:
            # Create default dataset file
            dataset_content = default_datasets[specialization]
            dataset_filename = f"default_{specialization}_dataset.jsonl"
            dataset_path = os.path.join(self.datasets_dir, f"{model.id}_{dataset_filename}")
            
            # Write JSONL file
            with open(dataset_path, 'w', encoding='utf-8') as f:
                for item in dataset_content:
                    f.write(json.dumps(item) + '\n')
            
            # Create database record
            dataset = TrainingDataset(
                model_id=model.id,
                filename=dataset_filename,
                file_path=dataset_path,
                file_size=os.path.getsize(dataset_path),
                dataset_type="jsonl",
                validation_status="valid",  # Pre-validated
                row_count=len(dataset_content),
                uploaded_by=user_id
            )
            
            db.add(dataset)
            db.commit()
            
            logger.info(f"Created default {specialization} dataset for model {model.id}")
            
        except Exception as e:
            logger.error(f"Failed to create default dataset for {specialization}: {e}")
            # Don't fail model creation if default dataset fails