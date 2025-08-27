import os
import json
# import torch
import asyncio
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
# from transformers import (
#     AutoTokenizer, AutoModelForCausalLM, TrainingArguments, 
#     Trainer, DataCollatorForLanguageModeling, EarlyStoppingCallback
# )
# from datasets import Dataset
# from peft import LoraConfig, get_peft_model, TaskType
import logging
from concurrent.futures import ThreadPoolExecutor

from models import FineTunedModel, TrainingDataset, FineTuningLog, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FineTuningService:
    """Service for managing fine-tuning operations"""
    
    def __init__(self):
        self.base_models_dir = os.getenv("BASE_MODELS_DIR", "/app/models/base")
        self.fine_tuned_models_dir = os.getenv("FINE_TUNED_MODELS_DIR", "/app/models/fine_tuned")
        self.datasets_dir = os.getenv("DATASETS_DIR", "/app/datasets")
        self.executor = ThreadPoolExecutor(max_workers=2)  # Limit concurrent training
        
        # Ensure directories exist
        os.makedirs(self.base_models_dir, exist_ok=True)
        os.makedirs(self.fine_tuned_models_dir, exist_ok=True)
        os.makedirs(self.datasets_dir, exist_ok=True)
        
        # Available base models configuration
        self.available_base_models = {
            "microsoft/DialoGPT-medium": {
                "name": "DialoGPT Medium",
                "description": "Conversational AI model good for general dialogue",
                "size": "350M parameters",
                "specializations": ["customer_service", "general_chat", "support"]
            },
            "microsoft/DialoGPT-small": {
                "name": "DialoGPT Small",
                "description": "Lightweight conversational model for quick training",
                "size": "117M parameters", 
                "specializations": ["customer_service", "faq", "simple_chat"]
            },
            "distilgpt2": {
                "name": "DistilGPT-2",
                "description": "Fast and efficient text generation model",
                "size": "82M parameters",
                "specializations": ["content_generation", "text_completion", "creative_writing"]
            }
        }
    
    async def get_available_base_models(self) -> Dict[str, Any]:
        """Get list of available base models for fine-tuning"""
        return self.available_base_models
    
    async def create_fine_tuned_model(
        self, 
        model_data: Dict[str, Any], 
        user_id: int, 
        db: Session
    ) -> FineTunedModel:
        """Create a new fine-tuned model record"""
        
        # Validate base model
        if model_data["base_model"] not in self.available_base_models:
            raise ValueError(f"Base model {model_data['base_model']} not supported")
        
        # Create model directory
        model_dir = os.path.join(
            self.fine_tuned_models_dir, 
            f"user_{user_id}", 
            f"{model_data['name'].replace(' ', '_').lower()}"
        )
        os.makedirs(model_dir, exist_ok=True)
        
        # Create model record
        fine_tuned_model = FineTunedModel(
            name=model_data["name"],
            description=model_data.get("description"),
            base_model=model_data["base_model"],
            model_path=model_dir,
            specialization=model_data.get("specialization"),
            owner_id=user_id,
            training_status="pending"
        )
        
        db.add(fine_tuned_model)
        db.commit()
        db.refresh(fine_tuned_model)
        
        # Log creation
        await self._log_training_event(
            fine_tuned_model.id, 
            "INFO", 
            f"Fine-tuned model '{model_data['name']}' created", 
            db
        )
        
        return fine_tuned_model
    
    async def upload_training_dataset(
        self,
        model_id: int,
        file_path: str,
        filename: str,
        dataset_type: str,
        user_id: int,
        db: Session
    ) -> TrainingDataset:
        """Upload and validate training dataset"""
        
        # Check if model exists and user has access
        model = db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id,
            FineTunedModel.owner_id == user_id
        ).first()
        
        if not model:
            raise ValueError("Model not found or access denied")
        
        # Get file size
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # Create dataset record
        dataset = TrainingDataset(
            model_id=model_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            dataset_type=dataset_type,
            uploaded_by=user_id
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # Validate dataset asynchronously
        asyncio.create_task(self._validate_dataset(dataset.id, db))
        
        return dataset
    
    async def _validate_dataset(self, dataset_id: int, db: Session):
        """Validate training dataset format and content"""
        
        dataset = db.query(TrainingDataset).filter(TrainingDataset.id == dataset_id).first()
        if not dataset:
            return
        
        try:
            errors = []
            row_count = 0
            
            if dataset.dataset_type == "jsonl":
                # Validate JSONL format for conversational data
                with open(dataset.file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            data = json.loads(line.strip())
                            if not isinstance(data, dict):
                                errors.append(f"Line {line_num}: Expected JSON object")
                            elif "input" not in data or "output" not in data:
                                errors.append(f"Line {line_num}: Missing 'input' or 'output' field")
                            row_count += 1
                        except json.JSONDecodeError:
                            errors.append(f"Line {line_num}: Invalid JSON format")
                        
                        if line_num > 10000:  # Limit validation for large files
                            break
            
            elif dataset.dataset_type == "csv":
                # Validate CSV format
                try:
                    df = pd.read_csv(dataset.file_path)
                    if "input" not in df.columns or "output" not in df.columns:
                        errors.append("CSV must contain 'input' and 'output' columns")
                    row_count = len(df)
                except Exception as e:
                    errors.append(f"CSV parsing error: {str(e)}")
            
            else:
                errors.append(f"Unsupported dataset type: {dataset.dataset_type}")
            
            # Update validation status
            if errors:
                dataset.validation_status = "invalid"
                dataset.validation_errors = "; ".join(errors)
            else:
                dataset.validation_status = "valid"
                dataset.row_count = row_count
            
            db.commit()
            
            # Log validation result
            await self._log_training_event(
                dataset.model_id,
                "INFO" if not errors else "WARNING",
                f"Dataset validation completed: {len(errors)} errors found",
                db
            )
            
        except Exception as e:
            dataset.validation_status = "invalid"
            dataset.validation_errors = f"Validation failed: {str(e)}"
            db.commit()
            
            await self._log_training_event(
                dataset.model_id,
                "ERROR",
                f"Dataset validation failed: {str(e)}",
                db
            )
    
    async def start_fine_tuning(
        self, 
        model_id: int, 
        training_params: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> bool:
        """Start fine-tuning process"""
        
        # Verify model ownership
        model = db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id,
            FineTunedModel.owner_id == user_id
        ).first()
        
        if not model:
            raise ValueError("Model not found or access denied")
        
        if model.training_status == "training":
            raise ValueError("Model is already being trained")
        
        # Check if datasets are valid
        datasets = db.query(TrainingDataset).filter(
            TrainingDataset.model_id == model_id,
            TrainingDataset.validation_status == "valid"
        ).all()
        
        if not datasets:
            raise ValueError("No valid training datasets found")
        
        # Update status
        model.training_status = "training"
        model.training_progress = 0
        db.commit()
        
        # Start training asynchronously
        asyncio.create_task(self._run_fine_tuning(model_id, datasets, training_params, db))
        
        return True
    
    async def _run_fine_tuning(
        self,
        model_id: int,
        datasets: List[TrainingDataset],
        training_params: Dict[str, Any],
        db: Session
    ):
        """Run the actual fine-tuning process"""
        
        model_record = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        
        try:
            await self._log_training_event(model_id, "INFO", "Starting fine-tuning process", db)
            
            # Load base model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_record.base_model)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            base_model = AutoModelForCausalLM.from_pretrained(
                model_record.base_model,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Configure LoRA for efficient fine-tuning
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=training_params.get("lora_r", 16),
                lora_alpha=training_params.get("lora_alpha", 32),
                lora_dropout=training_params.get("lora_dropout", 0.1),
                target_modules=training_params.get("target_modules", ["q_proj", "v_proj"])
            )
            
            model = get_peft_model(base_model, lora_config)
            model.print_trainable_parameters()
            
            # Prepare training data
            training_data = []
            for dataset in datasets:
                data = await self._load_dataset(dataset)
                training_data.extend(data)
            
            await self._log_training_event(
                model_id, 
                "INFO", 
                f"Loaded {len(training_data)} training examples", 
                db
            )
            
            # Create HuggingFace dataset
            train_dataset = Dataset.from_list(training_data)
            
            def tokenize_function(examples):
                # Combine input and output for language modeling
                texts = [f"{inp} {out}" for inp, out in zip(examples["input"], examples["output"])]
                return tokenizer(texts, truncation=True, padding=True, max_length=512)
            
            tokenized_dataset = train_dataset.map(tokenize_function, batched=True)
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=model_record.model_path,
                overwrite_output_dir=True,
                num_train_epochs=training_params.get("num_epochs", 3),
                per_device_train_batch_size=training_params.get("batch_size", 4),
                gradient_accumulation_steps=training_params.get("gradient_accumulation_steps", 2),
                learning_rate=training_params.get("learning_rate", 5e-5),
                warmup_steps=training_params.get("warmup_steps", 100),
                logging_steps=10,
                save_steps=100,
                eval_steps=100,
                save_total_limit=2,
                prediction_loss_only=True,
                remove_unused_columns=False,
                dataloader_pin_memory=False,
                load_best_model_at_end=True,
                metric_for_best_model="loss",
                greater_is_better=False,
                report_to=None  # Disable wandb/tensorboard
            )
            
            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False
            )
            
            # Custom trainer callback for progress tracking
            class ProgressCallback:
                def __init__(self, model_id, db):
                    self.model_id = model_id
                    self.db = db
                    self.step_count = 0
                
                def on_step_end(self, args, state, control, **kwargs):
                    self.step_count += 1
                    if self.step_count % 10 == 0:
                        # Update progress
                        progress = min(100, int((state.global_step / state.max_steps) * 100))
                        model = self.db.query(FineTunedModel).filter(FineTunedModel.id == self.model_id).first()
                        model.training_progress = progress
                        self.db.commit()
            
            # Initialize trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                tokenizer=tokenizer,
                data_collator=data_collator,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # Start training
            await self._log_training_event(model_id, "INFO", "Training started", db)
            
            # Run training in executor to avoid blocking
            train_result = await asyncio.get_event_loop().run_in_executor(
                self.executor, trainer.train
            )
            
            # Save model
            trainer.save_model()
            tokenizer.save_pretrained(model_record.model_path)
            
            # Update model record
            model_record.training_status = "completed"
            model_record.training_progress = 100
            model_record.completed_at = datetime.now(timezone.utc)
            model_record.loss_score = str(train_result.training_loss)
            
            # Calculate model size
            model_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(model_record.model_path)
                for filename in filenames
            )
            model_record.model_size = model_size
            
            db.commit()
            
            await self._log_training_event(
                model_id, 
                "INFO", 
                f"Fine-tuning completed successfully. Final loss: {train_result.training_loss:.4f}", 
                db
            )
            
        except Exception as e:
            logger.error(f"Fine-tuning failed for model {model_id}: {str(e)}")
            
            model_record.training_status = "failed"
            db.commit()
            
            await self._log_training_event(
                model_id, 
                "ERROR", 
                f"Fine-tuning failed: {str(e)}", 
                db
            )
    
    async def _load_dataset(self, dataset: TrainingDataset) -> List[Dict[str, str]]:
        """Load training data from dataset file"""
        
        data = []
        
        if dataset.dataset_type == "jsonl":
            with open(dataset.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line.strip())
                        data.append({
                            "input": item.get("input", ""),
                            "output": item.get("output", "")
                        })
                    except json.JSONDecodeError:
                        continue
        
        elif dataset.dataset_type == "csv":
            df = pd.read_csv(dataset.file_path)
            for _, row in df.iterrows():
                data.append({
                    "input": str(row.get("input", "")),
                    "output": str(row.get("output", ""))
                })
        
        return data
    
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
        """Log training event to database"""
        
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
        
        logger.info(f"[Model {model_id}] {level}: {message}")
    
    async def get_user_models(self, user_id: int, db: Session) -> List[FineTunedModel]:
        """Get all fine-tuned models for a user"""
        
        return db.query(FineTunedModel).filter(
            FineTunedModel.owner_id == user_id
        ).all()
    
    async def get_model_logs(
        self, 
        model_id: int, 
        user_id: int, 
        db: Session,
        limit: int = 100
    ) -> List[FineTuningLog]:
        """Get training logs for a specific model"""
        
        # Verify access
        model = db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id,
            FineTunedModel.owner_id == user_id
        ).first()
        
        if not model:
            raise ValueError("Model not found or access denied")
        
        return db.query(FineTuningLog).filter(
            FineTuningLog.model_id == model_id
        ).order_by(FineTuningLog.created_at.desc()).limit(limit).all()
    
    async def delete_model(self, model_id: int, user_id: int, db: Session) -> bool:
        """Delete a fine-tuned model and its files"""
        
        model = db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id,
            FineTunedModel.owner_id == user_id
        ).first()
        
        if not model:
            raise ValueError("Model not found or access denied")
        
        if model.training_status == "training":
            raise ValueError("Cannot delete model while training is in progress")
        
        try:
            # Delete model files
            import shutil
            if os.path.exists(model.model_path):
                shutil.rmtree(model.model_path)
            
            # Delete from database (cascading will handle related records)
            db.delete(model)
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_id}: {str(e)}")
            return False
    
    async def load_fine_tuned_model_for_inference(
        self, 
        model_id: int, 
        user_id: int, 
        db: Session
    ) -> Tuple[Optional[Any], Optional[Any]]:
        """Load a fine-tuned model for inference"""
        
        model = db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id,
            FineTunedModel.owner_id == user_id,
            FineTunedModel.training_status == "completed"
        ).first()
        
        if not model:
            return None, None
        
        try:
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model.model_path)
            fine_tuned_model = AutoModelForCausalLM.from_pretrained(
                model.model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            return fine_tuned_model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {str(e)}")
            return None, None