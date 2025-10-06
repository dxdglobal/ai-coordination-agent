"""
Dependencies - Task 1.3
========================

FastAPI dependency injection utilities for common functionality.
Provides reusable dependencies for authentication, database, pagination, and more.

Features:
- Database session dependencies
- Authentication dependencies
- Pagination dependencies
- Query parameter extraction
- Request validation
- Service injection

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

from typing import Optional, Dict, Any, List
from fastapi import Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database.connection import get_database_session
from database.schemas import PaginationSchema, SearchParams
from core.security import get_current_user, get_current_active_user, get_optional_user
from core.logging_config import get_logger
from database.models import User
from services import (
    get_user_service, get_client_service, get_project_service, get_task_service,
    UserService, ClientService, ProjectService, TaskService
)

# Configure logging
logger = get_logger(__name__)

# Database Dependencies
def get_db() -> Session:
    """
    Get database session dependency
    
    Returns:
        Database session
    """
    return get_database_session()

# Pagination Dependencies
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page")
) -> PaginationSchema:
    """
    Get pagination parameters from query string
    
    Args:
        page: Page number
        limit: Items per page limit
        
    Returns:
        Pagination schema
    """
    return PaginationSchema(page=page, limit=limit)

def get_search_params(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee_id: Optional[str] = Query(None, description="Filter by assignee ID"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date (after)"),
    created_before: Optional[datetime] = Query(None, description="Filter by creation date (before)"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)")
) -> SearchParams:
    """
    Get search parameters from query string
    
    Args:
        q: Search query
        status: Status filter
        priority: Priority filter
        assignee_id: Assignee ID filter
        created_after: Created after date filter
        created_before: Created before date filter
        sort_by: Sort field
        sort_order: Sort order
        
    Returns:
        Search parameters schema
    """
    return SearchParams(
        q=q,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        created_after=created_after,
        created_before=created_before,
        sort_by=sort_by,
        sort_order=sort_order
    )

# Service Dependencies
def get_user_service_dep(db: Session = Depends(get_db)) -> UserService:
    """
    Get UserService dependency
    
    Args:
        db: Database session
        
    Returns:
        UserService instance
    """
    return get_user_service(db)

def get_client_service_dep(db: Session = Depends(get_db)) -> ClientService:
    """
    Get ClientService dependency
    
    Args:
        db: Database session
        
    Returns:
        ClientService instance
    """
    return get_client_service(db)

def get_project_service_dep(db: Session = Depends(get_db)) -> ProjectService:
    """
    Get ProjectService dependency
    
    Args:
        db: Database session
        
    Returns:
        ProjectService instance
    """
    return get_project_service(db)

def get_task_service_dep(db: Session = Depends(get_db)) -> TaskService:
    """
    Get TaskService dependency
    
    Args:
        db: Database session
        
    Returns:
        TaskService instance
    """
    return get_task_service(db)

# Request Context Dependencies
def get_request_context(request: Request) -> Dict[str, Any]:
    """
    Get request context information
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request context dictionary
    """
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.utcnow()
    }

def get_client_info(request: Request) -> Dict[str, str]:
    """
    Get client information from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client information dictionary
    """
    return {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "origin": request.headers.get("origin", "unknown"),
        "referer": request.headers.get("referer", "unknown")
    }

# Validation Dependencies
def validate_uuid(entity_id: str) -> str:
    """
    Validate UUID format
    
    Args:
        entity_id: Entity ID to validate
        
    Returns:
        Validated entity ID
        
    Raises:
        HTTPException: If ID format is invalid
    """
    import uuid
    
    try:
        uuid.UUID(entity_id)
        return entity_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid ID format"
        )

def validate_positive_int(value: int, field_name: str = "value") -> int:
    """
    Validate positive integer
    
    Args:
        value: Integer to validate
        field_name: Field name for error message
        
    Returns:
        Validated integer
        
    Raises:
        HTTPException: If value is not positive
    """
    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be positive"
        )
    return value

# Filter Dependencies
def get_status_filter(
    status: Optional[str] = Query(None, description="Filter by status")
) -> Optional[str]:
    """Get status filter parameter"""
    return status

def get_priority_filter(
    priority: Optional[str] = Query(None, description="Filter by priority") 
) -> Optional[str]:
    """Get priority filter parameter"""
    return priority

def get_date_range_filter(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter")
) -> Dict[str, Optional[datetime]]:
    """
    Get date range filter parameters
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Date range dictionary
        
    Raises:
        HTTPException: If date range is invalid
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Start date cannot be after end date"
        )
    
    return {"start_date": start_date, "end_date": end_date}

# User Context Dependencies
def get_current_user_id(current_user: User = Depends(get_current_active_user)) -> str:
    """
    Get current user ID
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User ID
    """
    return current_user.id

def get_current_username(current_user: User = Depends(get_current_active_user)) -> str:
    """
    Get current username
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Username
    """
    return current_user.username

def get_user_permissions(current_user: User = Depends(get_current_active_user)) -> List[str]:
    """
    Get user permissions based on role
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of permissions
    """
    from database.models import UserRole
    
    permissions = []
    
    # Base permissions for all users
    permissions.extend([
        "read:own_profile",
        "update:own_profile",
        "read:assigned_tasks",
        "update:assigned_tasks"
    ])
    
    # Manager permissions
    if current_user.role in [UserRole.MANAGER, UserRole.ADMIN]:
        permissions.extend([
            "read:projects",
            "create:projects",
            "update:projects",
            "read:tasks", 
            "create:tasks",
            "update:tasks",
            "assign:tasks",
            "read:team_members"
        ])
    
    # Admin permissions
    if current_user.role == UserRole.ADMIN:
        permissions.extend([
            "read:all_users",
            "create:users",
            "update:users",
            "delete:users",
            "read:all_projects",
            "delete:projects",
            "read:all_tasks",
            "delete:tasks",
            "read:clients",
            "create:clients",
            "update:clients",
            "delete:clients",
            "read:system_stats",
            "manage:system"
        ])
    
    return permissions

# Query Optimization Dependencies
def get_includes(
    include: Optional[str] = Query(None, description="Comma-separated list of related objects to include")
) -> List[str]:
    """
    Get include parameters for query optimization
    
    Args:
        include: Comma-separated include string
        
    Returns:
        List of objects to include
    """
    if not include:
        return []
    
    return [item.strip() for item in include.split(",") if item.strip()]

def get_fields(
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to return")
) -> Optional[List[str]]:
    """
    Get field selection parameters
    
    Args:
        fields: Comma-separated fields string
        
    Returns:
        List of fields to return or None for all fields
    """
    if not fields:
        return None
    
    return [field.strip() for field in fields.split(",") if field.strip()]

# Cache Dependencies
def get_cache_key(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
) -> str:
    """
    Generate cache key for request
    
    Args:
        request: FastAPI request object
        current_user: Optional current user
        
    Returns:
        Cache key string
    """
    key_parts = [
        request.method,
        request.url.path,
        str(sorted(request.query_params.items())),
    ]
    
    if current_user:
        key_parts.append(f"user:{current_user.id}")
    
    import hashlib
    cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
    return cache_key

# Audit Dependencies  
def get_audit_context(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
) -> Dict[str, Any]:
    """
    Get audit context for operations
    
    Args:
        request: FastAPI request object
        current_user: Optional current user
        
    Returns:
        Audit context dictionary
    """
    context = {
        "timestamp": datetime.utcnow(),
        "operation": f"{request.method} {request.url.path}",
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    if current_user:
        context.update({
            "user_id": current_user.id,
            "username": current_user.username,
            "user_role": current_user.role
        })
    
    return context

# Resource Ownership Dependencies
def check_resource_ownership(resource_user_id: str, current_user: User = Depends(get_current_active_user)) -> bool:
    """
    Check if current user owns the resource
    
    Args:
        resource_user_id: User ID that owns the resource
        current_user: Current authenticated user
        
    Returns:
        True if user owns resource or is admin
        
    Raises:
        HTTPException: If user doesn't have access
    """
    from database.models import UserRole
    
    # Admin can access all resources
    if current_user.role == UserRole.ADMIN:
        return True
    
    # User can access their own resources
    if current_user.id == resource_user_id:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to access this resource"
    )

# Export dependencies
__all__ = [
    # Database
    "get_db",
    
    # Pagination and Search
    "get_pagination_params",
    "get_search_params",
    
    # Services
    "get_user_service_dep",
    "get_client_service_dep", 
    "get_project_service_dep",
    "get_task_service_dep",
    
    # Request Context
    "get_request_context",
    "get_client_info",
    
    # Validation
    "validate_uuid",
    "validate_positive_int",
    
    # Filters
    "get_status_filter",
    "get_priority_filter",
    "get_date_range_filter",
    
    # User Context
    "get_current_user_id",
    "get_current_username",
    "get_user_permissions",
    
    # Query Optimization
    "get_includes",
    "get_fields",
    
    # Cache and Audit
    "get_cache_key",
    "get_audit_context",
    
    # Resource Access
    "check_resource_ownership"
]