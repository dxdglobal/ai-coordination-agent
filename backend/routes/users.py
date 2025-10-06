"""
Users API Routes - Task 1.3
===========================

FastAPI routes for user management including:
- CRUD operations for users
- User authentication and authorization
- User profile management
- User task and project relationships
- Integration with CRM API

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database.connection import get_database_session
from database.models import User as DBUser, Task as DBTask, Project as DBProject
from schemas.user_schemas import (
    UserCreate, UserUpdate, UserResponse, 
    UserListResponse, UserWithTasks, UserLogin
)
from services.user_service import UserService
from core.dependencies import get_current_user, get_crm_client
from core.pagination import PaginationParams, paginate
from core.exceptions import UserNotFoundError, ValidationError, AuthenticationError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/",
    response_model=UserListResponse,
    summary="Get all users",
    description="Retrieve a paginated list of users with optional filtering"
)
async def get_users(
    pagination: PaginationParams = Depends(),
    role: Optional[str] = Query(None, description="Filter by user role"),
    department: Optional[str] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name/email"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all users with optional filtering and pagination.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 50, max: 100)
    - **role**: Filter by user role (admin, manager, user, client)
    - **department**: Filter by department
    - **is_active**: Filter by active status
    - **search**: Search term for name/email
    """
    try:
        logger.info(f"Getting users for user {current_user.get('id')} with filters")
        
        service = UserService(db)
        
        filters = {}
        if role:
            filters['role'] = role
        if department:
            filters['department'] = department
        if is_active is not None:
            filters['is_active'] = is_active
        if search:
            filters['search'] = search
        
        users, total_count = service.get_users_paginated(
            page=pagination.page,
            size=pagination.size,
            filters=filters
        )
        
        return UserListResponse(
            data=users,
            total=total_count,
            page=pagination.page,
            size=pagination.size,
            pages=(total_count + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID"
)
async def get_user(
    user_id: int = Path(..., description="User ID"),
    include_tasks: bool = Query(False, description="Include user's tasks"),
    include_projects: bool = Query(False, description="Include user's projects"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific user by ID.
    
    - **user_id**: The ID of the user to retrieve
    - **include_tasks**: Whether to include user's tasks in response
    - **include_projects**: Whether to include user's projects in response
    """
    try:
        logger.info(f"Getting user {user_id} for user {current_user.get('id')}")
        
        service = UserService(db)
        user = service.get_user_by_id(
            user_id, 
            include_tasks=include_tasks,
            include_projects=include_projects
        )
        
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return UserResponse(data=user)
        
    except UserNotFoundError as e:
        logger.warning(f"User not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create a new user"
)
async def create_user(
    user_data: UserCreate,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Create a new user.
    
    - **username**: Username (required, unique)
    - **email**: Email address (required, unique)
    - **first_name**: First name
    - **last_name**: Last name
    - **password**: Password (required)
    - **role**: User role (default: user)
    - **department**: Department
    - **position**: Job position
    - **phone**: Phone number
    """
    try:
        logger.info(f"Creating user '{user_data.username}' by user {current_user.get('id')}")
        
        service = UserService(db)
        
        # Create user in database
        user = service.create_user(user_data, creator_id=current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client:
            try:
                from crm_api_endpoints import User as CRMUser
                crm_user = CRMUser(
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=user.role,
                    department=user.department,
                    position=user.position,
                    phone=user.phone,
                    is_active=user.is_active
                )
                
                crm_response = crm_client.users.create(crm_user)
                service.update_crm_id(user.id, crm_response.id)
                logger.info(f"User {user.id} synced to CRM with ID {crm_response.id}")
                
            except Exception as e:
                logger.warning(f"Failed to sync user to CRM: {e}")
        
        return UserResponse(
            data=user,
            message="User created successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update an existing user"
)
async def update_user(
    user_id: int = Path(..., description="User ID"),
    user_data: UserUpdate = ...,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Update an existing user.
    
    - **user_id**: The ID of the user to update
    - Only provided fields will be updated
    """
    try:
        logger.info(f"Updating user {user_id} by user {current_user.get('id')}")
        
        service = UserService(db)
        
        # Check if user exists
        existing_user = service.get_user_by_id(user_id)
        if not existing_user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Check permissions (users can only update themselves unless admin)
        if current_user.get('id') != user_id and current_user.get('role') != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this user"
            )
        
        # Update user
        user = service.update_user(user_id, user_data, updater_id=current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client and user.crm_id:
            try:
                from crm_api_endpoints import User as CRMUser
                crm_user = CRMUser(
                    id=user.crm_id,
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=user.role,
                    department=user.department,
                    position=user.position,
                    phone=user.phone,
                    is_active=user.is_active
                )
                
                crm_client.users.update(user.crm_id, crm_user)
                logger.info(f"User {user.id} synced to CRM")
                
            except Exception as e:
                logger.warning(f"Failed to sync user update to CRM: {e}")
        
        return UserResponse(
            data=user,
            message="User updated successfully"
        )
        
    except UserNotFoundError as e:
        logger.warning(f"User not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Validation error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user (soft delete - sets is_active to False)"
)
async def delete_user(
    user_id: int = Path(..., description="User ID"),
    sync_to_crm: bool = Query(True, description="Sync deletion to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Delete a user (soft delete - sets is_active to False).
    
    - **user_id**: The ID of the user to delete
    - This performs a soft delete by setting is_active to False
    """
    try:
        logger.info(f"Deleting user {user_id} by user {current_user.get('id')}")
        
        # Check permissions (only admins can delete users)
        if current_user.get('role') != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete users"
            )
        
        service = UserService(db)
        
        # Check if user exists
        user = service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Prevent self-deletion
        if user_id == current_user.get('id'):
            raise ValidationError("Cannot delete your own account")
        
        # Sync to CRM first if needed (deactivate user)
        if sync_to_crm and crm_client and user.crm_id:
            try:
                from crm_api_endpoints import User as CRMUser
                crm_user = CRMUser(
                    id=user.crm_id,
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=user.role,
                    department=user.department,
                    position=user.position,
                    phone=user.phone,
                    is_active=False
                )
                crm_client.users.update(user.crm_id, crm_user)
                logger.info(f"User {user_id} deactivated in CRM")
            except Exception as e:
                logger.warning(f"Failed to deactivate user in CRM: {e}")
        
        # Soft delete from database
        service.delete_user(user_id, deleter_id=current_user.get('id'))
        
        logger.info(f"User {user_id} deleted successfully")
        
    except UserNotFoundError as e:
        logger.warning(f"User not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.get(
    "/{user_id}/tasks",
    response_model=List[Dict[str, Any]],
    summary="Get user's tasks",
    description="Get all tasks assigned to a specific user"
)
async def get_user_tasks(
    user_id: int = Path(..., description="User ID"),
    status_filter: Optional[str] = Query(None, description="Filter by task status"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all tasks assigned to a specific user.
    
    - **user_id**: The ID of the user
    - **status**: Filter by task status
    - **project_id**: Filter by project ID
    """
    try:
        logger.info(f"Getting tasks for user {user_id}")
        
        service = UserService(db)
        
        # Check if user exists
        user = service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        filters = {"assignee_id": user_id}
        if status_filter:
            filters["status"] = status_filter
        if project_id:
            filters["project_id"] = project_id
        
        tasks = service.get_user_tasks(user_id, filters)
        
        return tasks
        
    except UserNotFoundError as e:
        logger.warning(f"User not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting tasks for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user tasks: {str(e)}"
        )

@router.get(
    "/{user_id}/projects",
    response_model=List[Dict[str, Any]],
    summary="Get user's projects",
    description="Get all projects where the user is a manager or team member"
)
async def get_user_projects(
    user_id: int = Path(..., description="User ID"),
    role_filter: Optional[str] = Query(None, description="Filter by user role in project (manager, member)"),
    status_filter: Optional[str] = Query(None, description="Filter by project status"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all projects where the user is involved.
    
    - **user_id**: The ID of the user
    - **role**: Filter by user role in project (manager, member)
    - **status**: Filter by project status
    """
    try:
        logger.info(f"Getting projects for user {user_id}")
        
        service = UserService(db)
        
        # Check if user exists
        user = service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        filters = {}
        if role_filter:
            filters["role"] = role_filter
        if status_filter:
            filters["status"] = status_filter
        
        projects = service.get_user_projects(user_id, filters)
        
        return projects
        
    except UserNotFoundError as e:
        logger.warning(f"User not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting projects for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user projects: {str(e)}"
        )

@router.post(
    "/login",
    response_model=Dict[str, Any],
    summary="User login",
    description="Authenticate user and return access token"
)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_database_session)
):
    """
    Authenticate user and return access token.
    
    - **username**: Username or email
    - **password**: User password
    """
    try:
        logger.info(f"Login attempt for user: {login_data.username}")
        
        service = UserService(db)
        
        # Authenticate user
        user, token = service.authenticate_user(login_data.username, login_data.password)
        
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        logger.info(f"User {user.id} logged in successfully")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "department": user.department
            },
            "message": "Login successful"
        }
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post(
    "/logout",
    summary="User logout",
    description="Logout user and invalidate token"
)
async def logout_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Logout user and invalidate token.
    """
    try:
        logger.info(f"User {current_user.get('id')} logging out")
        
        service = UserService(db)
        
        # Update last login time
        service.update_last_logout(current_user.get('id'))
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get current authenticated user's profile"
)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Get current authenticated user's profile.
    """
    try:
        user_id = current_user.get('id')
        logger.info(f"Getting profile for current user {user_id}")
        
        service = UserService(db)
        user = service.get_user_by_id(user_id, include_tasks=True, include_projects=True)
        
        if not user:
            raise UserNotFoundError("Current user not found")
        
        return UserResponse(data=user)
        
    except UserNotFoundError as e:
        logger.warning(f"User not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting current user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )