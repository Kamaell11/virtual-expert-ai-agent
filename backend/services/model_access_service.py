from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from models import FineTunedModel, User, UserModelAccess
import logging

logger = logging.getLogger(__name__)

class ModelAccessService:
    """Service for managing model access permissions and isolation between clients"""
    
    def __init__(self):
        self.model_cache = {}  # Cache for loaded models per user
    
    async def get_user_accessible_models(
        self, 
        user_id: int, 
        db: Session,
        include_owned: bool = True,
        include_shared: bool = True,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all models accessible to a user (owned + shared)"""
        
        models = []
        
        if include_owned:
            # Get user's own models
            owned_models = db.query(FineTunedModel).filter(
                FineTunedModel.owner_id == user_id,
                FineTunedModel.is_active == True
            )
            
            if status_filter:
                owned_models = owned_models.filter(FineTunedModel.training_status == status_filter)
            
            for model in owned_models.all():
                models.append({
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "base_model": model.base_model,
                    "specialization": model.specialization,
                    "training_status": model.training_status,
                    "training_progress": model.training_progress,
                    "access_type": "owner",
                    "access_level": "admin",
                    "model_size": model.model_size,
                    "created_at": model.created_at,
                    "completed_at": model.completed_at
                })
        
        if include_shared:
            # Get models shared with the user
            shared_access = db.query(UserModelAccess).join(FineTunedModel).filter(
                UserModelAccess.user_id == user_id,
                UserModelAccess.is_active == True,
                FineTunedModel.is_active == True
            )
            
            # Check expiration
            current_time = datetime.now(timezone.utc)
            shared_access = shared_access.filter(
                (UserModelAccess.expires_at.is_(None)) | 
                (UserModelAccess.expires_at > current_time)
            )
            
            if status_filter:
                shared_access = shared_access.filter(FineTunedModel.training_status == status_filter)
            
            for access in shared_access.all():
                model = access.model
                models.append({
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "base_model": model.base_model,
                    "specialization": model.specialization,
                    "training_status": model.training_status,
                    "training_progress": model.training_progress,
                    "access_type": "shared",
                    "access_level": access.access_level,
                    "model_size": model.model_size,
                    "created_at": model.created_at,
                    "completed_at": model.completed_at,
                    "shared_by": model.owner.username,
                    "expires_at": access.expires_at
                })
        
        return models
    
    async def check_model_access(
        self, 
        user_id: int, 
        model_id: int, 
        required_access: str,
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has required access to a model
        
        Args:
            user_id: User ID to check
            model_id: Model ID to check access for
            required_access: 'read', 'write', or 'admin'
            db: Database session
        
        Returns:
            Tuple of (has_access, access_level)
        """
        
        # Check if user owns the model
        owned_model = db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id,
            FineTunedModel.owner_id == user_id,
            FineTunedModel.is_active == True
        ).first()
        
        if owned_model:
            return True, "admin"  # Owners have admin access
        
        # Check shared access
        current_time = datetime.now(timezone.utc)
        shared_access = db.query(UserModelAccess).filter(
            UserModelAccess.user_id == user_id,
            UserModelAccess.model_id == model_id,
            UserModelAccess.is_active == True
        ).filter(
            (UserModelAccess.expires_at.is_(None)) | 
            (UserModelAccess.expires_at > current_time)
        ).first()
        
        if not shared_access:
            return False, None
        
        # Check access level hierarchy: admin > write > read
        access_levels = {"read": 1, "write": 2, "admin": 3}
        user_level = access_levels.get(shared_access.access_level, 0)
        required_level = access_levels.get(required_access, 0)
        
        if user_level >= required_level:
            return True, shared_access.access_level
        
        return False, shared_access.access_level
    
    async def grant_model_access(
        self,
        granter_id: int,
        target_user_id: int,
        model_id: int,
        access_level: str,
        expires_at: Optional[datetime],
        db: Session
    ) -> UserModelAccess:
        """Grant access to a model for another user"""
        
        # Verify granter has admin access
        has_access, current_level = await self.check_model_access(
            granter_id, model_id, "admin", db
        )
        
        if not has_access:
            raise ValueError("You don't have permission to grant access to this model")
        
        # Check if target user exists
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise ValueError("Target user not found")
        
        # Check if access already exists
        existing_access = db.query(UserModelAccess).filter(
            UserModelAccess.user_id == target_user_id,
            UserModelAccess.model_id == model_id,
            UserModelAccess.is_active == True
        ).first()
        
        if existing_access:
            # Update existing access
            existing_access.access_level = access_level
            existing_access.expires_at = expires_at
            existing_access.granted_by = granter_id
            existing_access.granted_at = datetime.now(timezone.utc)
            db.commit()
            return existing_access
        else:
            # Create new access
            new_access = UserModelAccess(
                user_id=target_user_id,
                model_id=model_id,
                access_level=access_level,
                expires_at=expires_at,
                granted_by=granter_id
            )
            db.add(new_access)
            db.commit()
            db.refresh(new_access)
            return new_access
    
    async def revoke_model_access(
        self,
        revoker_id: int,
        target_user_id: int,
        model_id: int,
        db: Session
    ) -> bool:
        """Revoke model access for a user"""
        
        # Verify revoker has admin access
        has_access, _ = await self.check_model_access(revoker_id, model_id, "admin", db)
        if not has_access:
            raise ValueError("You don't have permission to revoke access to this model")
        
        # Find and deactivate access
        access = db.query(UserModelAccess).filter(
            UserModelAccess.user_id == target_user_id,
            UserModelAccess.model_id == model_id,
            UserModelAccess.is_active == True
        ).first()
        
        if access:
            access.is_active = False
            db.commit()
            
            # Clear from model cache if loaded
            cache_key = f"{target_user_id}_{model_id}"
            if cache_key in self.model_cache:
                del self.model_cache[cache_key]
            
            return True
        
        return False
    
    async def get_model_access_list(
        self,
        requester_id: int,
        model_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get list of users who have access to a model"""
        
        # Verify requester has admin access
        has_access, _ = await self.check_model_access(requester_id, model_id, "admin", db)
        if not has_access:
            raise ValueError("You don't have permission to view model access list")
        
        # Get model owner info
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        if not model:
            raise ValueError("Model not found")
        
        access_list = []
        
        # Add owner
        access_list.append({
            "user_id": model.owner_id,
            "username": model.owner.username,
            "access_level": "admin",
            "access_type": "owner",
            "granted_at": model.created_at,
            "expires_at": None,
            "is_active": True
        })
        
        # Add shared access users
        current_time = datetime.now(timezone.utc)
        shared_accesses = db.query(UserModelAccess).join(User).filter(
            UserModelAccess.model_id == model_id,
            UserModelAccess.is_active == True
        ).all()
        
        for access in shared_accesses:
            is_expired = access.expires_at and access.expires_at < current_time
            access_list.append({
                "user_id": access.user_id,
                "username": access.user.username,
                "access_level": access.access_level,
                "access_type": "shared",
                "granted_at": access.granted_at,
                "expires_at": access.expires_at,
                "is_active": not is_expired,
                "granted_by": access.granter.username if access.granter else None
            })
        
        return access_list
    
    async def get_user_models_by_specialization(
        self,
        user_id: int,
        specialization: str,
        db: Session,
        status: str = "completed"
    ) -> List[Dict[str, Any]]:
        """Get user's models filtered by specialization"""
        
        all_models = await self.get_user_accessible_models(
            user_id, db, status_filter=status
        )
        
        # Filter by specialization
        specialized_models = [
            model for model in all_models 
            if model.get("specialization", "").lower() == specialization.lower()
        ]
        
        return specialized_models
    
    async def create_model_usage_log(
        self,
        user_id: int,
        model_id: int,
        query_text: str,
        response_text: str,
        db: Session
    ):
        """Log model usage for monitoring and billing"""
        
        # This could be extended to track usage statistics
        # For now, we'll use the existing Query/Response tables
        # In production, you might want a separate usage tracking table
        pass
    
    async def cleanup_expired_access(self, db: Session) -> int:
        """Clean up expired model access permissions"""
        
        current_time = datetime.now(timezone.utc)
        expired_count = db.query(UserModelAccess).filter(
            UserModelAccess.expires_at < current_time,
            UserModelAccess.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        
        # Clear expired entries from cache
        if expired_count > 0:
            self.model_cache.clear()  # Simple approach - clear entire cache
        
        return expired_count
    
    async def get_model_statistics(
        self,
        user_id: int,
        model_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get usage statistics for a model"""
        
        # Verify access
        has_access, _ = await self.check_model_access(user_id, model_id, "read", db)
        if not has_access:
            raise ValueError("Access denied")
        
        model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
        if not model:
            raise ValueError("Model not found")
        
        # Calculate basic statistics
        from models import Query, Response
        
        # Count queries using this model (approximation)
        query_count = db.query(Query).join(Response).filter(
            Response.model_used.contains(model.name)  # This is approximate
        ).count()
        
        stats = {
            "model_id": model_id,
            "model_name": model.name,
            "training_status": model.training_status,
            "model_size_bytes": model.model_size,
            "created_at": model.created_at,
            "completed_at": model.completed_at,
            "total_queries": query_count,
            "specialization": model.specialization,
            "base_model": model.base_model
        }
        
        return stats