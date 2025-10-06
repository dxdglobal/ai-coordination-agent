"""
Authentication & Security - Task 1.3
=====================================

Authentication, authorization, and security utilities for the AI Coordination Agent.
JWT token handling, password security, and access control.

Features:
- JWT token generation and validation
- Password hashing and verification
- Role-based access control
- API key authentication
- Security middleware
- Rate limiting

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import os
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import time

from core.logging_config import get_logger
from core.exceptions import AuthenticationException, AuthorizationException
from database.models import User, UserRole, UserStatus
from database.connection import get_database_session
from sqlalchemy.orm import Session

# Configure logging
logger = get_logger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token scheme
security = HTTPBearer()

class TokenManager:
    """JWT token management"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.debug(
            "Access token created",
            extra={
                "user_id": data.get("sub"),
                "expires_at": expire.isoformat()
            }
        )
        
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token
        
        Args:
            data: Token payload data
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.debug(
            "Refresh token created",
            extra={
                "user_id": data.get("sub"),
                "expires_at": expire.isoformat()
            }
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            token_type: Expected token type (access/refresh)
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise AuthenticationException("Invalid token type")
            
            # Verify expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise AuthenticationException("Token has expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationException("Token has expired")
        except jwt.JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise AuthenticationException("Invalid token")
    
    def get_user_from_token(self, token: str, db: Session) -> User:
        """
        Get user from JWT token
        
        Args:
            token: JWT token
            db: Database session
            
        Returns:
            User instance
            
        Raises:
            AuthenticationException: If token is invalid or user not found
        """
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationException("Invalid token payload")
        
        user = db.query(User).filter(
            User.id == user_id,
            User.status == UserStatus.ACTIVE,
            User.is_deleted == False
        ).first()
        
        if not user:
            raise AuthenticationException("User not found or inactive")
        
        return user

# Global token manager instance
token_manager = TokenManager()

class PasswordManager:
    """Password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """
        Generate secure random password
        
        Args:
            length: Password length
            
        Returns:
            Generated password
        """
        return secrets.token_urlsafe(length)

class RoleChecker:
    """Role-based access control"""
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Check if user has required role
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            User if authorized
            
        Raises:
            AuthorizationException: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles:
            logger.warning(
                f"Access denied for user {current_user.id} with role {current_user.role}",
                extra={
                    "user_id": current_user.id,
                    "user_role": current_user.role,
                    "required_roles": [role.value for role in self.allowed_roles]
                }
            )
            raise AuthorizationException(
                f"Insufficient permissions. Required roles: {[role.value for role in self.allowed_roles]}"
            )
        
        return current_user

# Rate limiting
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {client_id: [timestamp, ...]}
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if request is allowed
        """
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] 
                if req_time > minute_ago
            ]
        else:
            self.requests[client_id] = []
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        AuthenticationException: If authentication fails
    """
    try:
        token = credentials.credentials
        user = token_manager.get_user_from_token(token, db)
        
        logger.debug(
            "User authenticated",
            extra={
                "user_id": user.id,
                "username": user.username
            }
        )
        
        return user
        
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise AuthenticationException("Could not validate credentials")

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user
        
    Raises:
        AuthenticationException: If user is not active
    """
    if current_user.status != UserStatus.ACTIVE:
        raise AuthenticationException("User account is not active")
    
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_database_session)
) -> Optional[User]:
    """
    Get current user if token is provided (optional authentication)
    
    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session
        
    Returns:
        Current user or None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except AuthenticationException:
        return None

def require_roles(*roles: UserRole):
    """
    Decorator to require specific roles
    
    Args:
        roles: Required user roles
        
    Returns:
        Role checker dependency
    """
    return RoleChecker(list(roles))

def require_admin():
    """Require admin role"""
    return require_roles(UserRole.ADMIN)

def require_manager():
    """Require manager or admin role"""
    return require_roles(UserRole.MANAGER, UserRole.ADMIN)

async def check_rate_limit(request: Request):
    """
    Check rate limit for request
    
    Args:
        request: FastAPI request
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(
            f"Rate limit exceeded for {client_ip}",
            extra={"client_ip": client_ip}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

class APIKeyManager:
    """API key authentication manager"""
    
    def __init__(self):
        self.api_keys = {}  # In production, store in database
    
    def generate_api_key(self, user_id: str, name: str = None) -> str:
        """
        Generate API key for user
        
        Args:
            user_id: User ID
            name: Optional key name
            
        Returns:
            Generated API key
        """
        api_key = f"aica_{secrets.token_urlsafe(32)}"
        self.api_keys[api_key] = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.utcnow(),
            "last_used": None
        }
        
        logger.info(
            f"API key generated for user {user_id}",
            extra={"user_id": user_id, "key_name": name}
        )
        
        return api_key
    
    def validate_api_key(self, api_key: str, db: Session) -> Optional[User]:
        """
        Validate API key and return user
        
        Args:
            api_key: API key to validate
            db: Database session
            
        Returns:
            User if valid, None otherwise
        """
        if api_key not in self.api_keys:
            return None
        
        key_info = self.api_keys[api_key]
        user_id = key_info["user_id"]
        
        # Update last used
        key_info["last_used"] = datetime.utcnow()
        
        # Get user
        user = db.query(User).filter(
            User.id == user_id,
            User.status == UserStatus.ACTIVE,
            User.is_deleted == False
        ).first()
        
        return user

# Global API key manager
api_key_manager = APIKeyManager()

# Security utility functions
def generate_secure_token(length: int = 32) -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(length)

def hash_string(value: str) -> str:
    """Hash string with SHA-256"""
    return hashlib.sha256(value.encode()).hexdigest()

def constant_time_compare(a: str, b: str) -> bool:
    """Constant time string comparison"""
    return secrets.compare_digest(a, b)

# Export authentication utilities
__all__ = [
    # Main classes
    "TokenManager",
    "PasswordManager", 
    "RoleChecker",
    "RateLimiter",
    "APIKeyManager",
    
    # Instances
    "token_manager",
    "rate_limiter",
    "api_key_manager",
    
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_roles",
    "require_admin",
    "require_manager",
    "check_rate_limit",
    
    # Utilities
    "generate_secure_token",
    "hash_string",
    "constant_time_compare"
]