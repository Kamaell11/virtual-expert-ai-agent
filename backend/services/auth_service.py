from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from models import User
from schemas import UserCreate, UserResponse

load_dotenv()

class AuthService:
    """Service for user authentication and authorization"""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        # Convert hours to minutes for backward compatibility
        expire_hours = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
        expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(expire_hours * 60)))
        self.access_token_expire_minutes = expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            return {"username": username}
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def authenticate_user(self, user_data: UserCreate, db: Session):
        """Authenticate user and return access token"""
        user = self.get_user_by_username(db, user_data.username)
        if not user or not self.verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active
            }
        }
    
    def create_user(self, user_data: UserCreate, db: Session) -> UserResponse:
        """Create a new user"""
        # Check if username already exists
        if self.get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists (if provided)
        if user_data.email and self.get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = self.get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    
    def get_current_user(self, token: str, db: Session) -> User:
        """Get current user from JWT token"""
        token_data = self.verify_token(token)
        user = self.get_user_by_username(db, token_data["username"])
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        return user
    
    def update_user_password(self, user_id: int, new_password: str, db: Session) -> bool:
        """Update user password"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.hashed_password = self.get_password_hash(new_password)
        db.commit()
        return True
    
    def deactivate_user(self, user_id: int, db: Session) -> bool:
        """Deactivate user account"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        db.commit()
        return True