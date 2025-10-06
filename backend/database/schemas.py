"""
Pydantic Schemas - Task 1.3
============================

Pydantic models for request/response validation and serialization.
Comprehensive schemas for all API endpoints with proper validation rules.

Features:
- Request/response schemas for all models
- Data validation and serialization
- Nested relationships and computed fields
- CRM integration schemas
- Error response schemas
- Pagination and filtering schemas

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, validator, root_validator
from enum import Enum

# Enum classes for validation
class UserRoleSchema(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    CLIENT = "client"
    VIEWER = "viewer"

class UserStatusSchema(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class ProjectStatusSchema(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class ProjectPrioritySchema(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatusSchema(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPrioritySchema(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ClientStatusSchema(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    FORMER = "former"

class CommentTypeSchema(str, Enum):
    AI_GENERATED = "ai_generated"
    HUMAN_FEEDBACK = "human_feedback"
    SYSTEM = "system"
    NOTIFICATION = "notification"

# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None,
        }

class PaginationSchema(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    
class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    data: List[Any]
    total: int
    page: int
    limit: int
    pages: int

# User Schemas
class UserBase(BaseModel):
    """Base user fields"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    role: UserRoleSchema = UserRoleSchema.USER
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=255)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    role: Optional[UserRoleSchema] = None
    status: Optional[UserStatusSchema] = None
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(BaseSchema):
    """Schema for user response"""
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: UserRoleSchema
    status: UserStatusSchema
    last_login: Optional[datetime] = None
    timezone: str
    language: str
    preferences: Optional[Dict[str, Any]] = None
    crm_user_id: Optional[str] = None

class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str

class UserToken(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

# Client Schemas
class ClientBase(BaseModel):
    """Base client fields"""
    name: str = Field(..., min_length=1, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    """Schema for creating a new client"""
    status: ClientStatusSchema = ClientStatusSchema.ACTIVE

class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    status: Optional[ClientStatusSchema] = None
    notes: Optional[str] = None
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)

class ClientResponse(BaseSchema):
    """Schema for client response"""
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    annual_revenue: Optional[Decimal] = None
    status: ClientStatusSchema
    acquisition_date: Optional[date] = None
    notes: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    crm_client_id: Optional[str] = None
    project_count: Optional[int] = 0

# Project Schemas
class ProjectBase(BaseModel):
    """Base project fields"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    code: Optional[str] = Field(None, max_length=20)
    priority: ProjectPrioritySchema = ProjectPrioritySchema.MEDIUM
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    estimated_hours: Optional[int] = Field(None, ge=0)

class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""
    client_id: Optional[str] = None
    manager_id: Optional[str] = None
    status: ProjectStatusSchema = ProjectStatusSchema.PLANNING

class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    code: Optional[str] = Field(None, max_length=20)
    status: Optional[ProjectStatusSchema] = None
    priority: Optional[ProjectPrioritySchema] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    client_id: Optional[str] = None
    manager_id: Optional[str] = None

class ProjectResponse(BaseSchema):
    """Schema for project response"""
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    status: ProjectStatusSchema
    priority: ProjectPrioritySchema
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    estimated_hours: Optional[int] = None
    actual_hours: int = 0
    completion_percentage: int = 0
    last_activity_date: Optional[datetime] = None
    client_id: Optional[str] = None
    manager_id: Optional[str] = None
    crm_project_id: Optional[str] = None
    task_count: Optional[int] = 0
    is_active: Optional[bool] = None
    is_overdue: Optional[bool] = None
    
    # Nested objects
    client: Optional["ClientResponse"] = None
    manager: Optional["UserResponse"] = None

# Task Schemas
class TaskBase(BaseModel):
    """Base task fields"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: TaskPrioritySchema = TaskPrioritySchema.MEDIUM
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    tags: Optional[List[str]] = Field(default_factory=list)
    labels: Optional[List[str]] = Field(default_factory=list)

class TaskCreate(TaskBase):
    """Schema for creating a new task"""
    project_id: str
    assignee_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    status: TaskStatusSchema = TaskStatusSchema.TODO

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatusSchema] = None
    priority: Optional[TaskPrioritySchema] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    assignee_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    tags: Optional[List[str]] = None
    labels: Optional[List[str]] = None

class TaskResponse(BaseSchema):
    """Schema for task response"""
    title: str
    description: Optional[str] = None
    status: TaskStatusSchema
    priority: TaskPrioritySchema
    project_id: str
    assignee_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = None
    actual_hours: Decimal = 0
    completion_percentage: int = 0
    tags: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    crm_task_id: Optional[str] = None
    subtask_count: Optional[int] = 0
    is_overdue: Optional[bool] = None
    is_blocked: Optional[bool] = None
    
    # Nested objects
    project: Optional["ProjectResponse"] = None
    assignee: Optional["UserResponse"] = None
    parent_task: Optional["TaskResponse"] = None

# Comment Schemas
class CommentBase(BaseModel):
    """Base comment fields"""
    content: str = Field(..., min_length=1)
    comment_type: CommentTypeSchema = CommentTypeSchema.AI_GENERATED

class CommentCreate(CommentBase):
    """Schema for creating a new comment"""
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    ai_model: Optional[str] = None
    ai_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    ai_context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class CommentUpdate(BaseModel):
    """Schema for updating a comment"""
    content: Optional[str] = Field(None, min_length=1)
    is_helpful: Optional[bool] = None
    feedback_score: Optional[int] = Field(None, ge=1, le=5)
    human_feedback: Optional[str] = None

class CommentResponse(BaseSchema):
    """Schema for comment response"""
    content: str
    comment_type: CommentTypeSchema
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    ai_model: Optional[str] = None
    ai_confidence: Optional[Decimal] = None
    ai_context: Optional[Dict[str, Any]] = None
    is_helpful: Optional[bool] = None
    feedback_score: Optional[int] = None
    human_feedback: Optional[str] = None
    
    # Nested objects
    user: Optional["UserResponse"] = None

# Search and Filter Schemas
class SearchParams(BaseModel):
    """Search parameters"""
    q: Optional[str] = Field(None, description="Search query")
    status: Optional[str] = Field(None, description="Filter by status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    assignee_id: Optional[str] = Field(None, description="Filter by assignee")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")
    sort_by: Optional[str] = Field(default="created_at", description="Sort field")
    sort_order: Optional[str] = Field(default="desc", description="Sort order (asc/desc)")

class ProjectSearchParams(SearchParams):
    """Project-specific search parameters"""
    client_id: Optional[str] = Field(None, description="Filter by client")
    manager_id: Optional[str] = Field(None, description="Filter by manager")
    start_date_after: Optional[date] = Field(None, description="Filter by start date")
    end_date_before: Optional[date] = Field(None, description="Filter by end date")

class TaskSearchParams(SearchParams):
    """Task-specific search parameters"""
    project_id: Optional[str] = Field(None, description="Filter by project")
    due_date_before: Optional[datetime] = Field(None, description="Filter by due date")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    labels: Optional[List[str]] = Field(None, description="Filter by labels")

# Statistics and Analytics Schemas
class ProjectStatistics(BaseModel):
    """Project statistics"""
    total_projects: int
    active_projects: int
    completed_projects: int
    overdue_projects: int
    total_budget: Optional[Decimal] = None
    total_hours: int
    completion_rate: Optional[float] = None

class TaskStatistics(BaseModel):
    """Task statistics"""
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    completion_rate: Optional[float] = None
    average_completion_time: Optional[float] = None

class UserStatistics(BaseModel):
    """User statistics"""
    total_users: int
    active_users: int
    assigned_tasks: int
    completed_tasks: int
    managed_projects: int

class ClientStatistics(BaseModel):
    """Client statistics"""
    total_clients: int
    active_clients: int
    total_projects: int
    total_revenue: Optional[Decimal] = None

# Error Response Schemas
class ErrorDetail(BaseModel):
    """Error detail schema"""
    type: str
    msg: str
    loc: Optional[List[str]] = None

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: Union[str, List[ErrorDetail]]
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""
    errors: List[ErrorDetail]

# CRM Integration Schemas
class CRMSyncRequest(BaseModel):
    """CRM synchronization request"""
    entity_type: str = Field(..., description="Type of entity to sync")
    entity_id: str = Field(..., description="ID of entity to sync")
    operation: str = Field(..., description="Sync operation")
    force: bool = Field(default=False, description="Force sync even if recently synced")

class CRMSyncResponse(BaseModel):
    """CRM synchronization response"""
    sync_id: str
    status: str
    message: str
    entity_type: str
    entity_id: str
    crm_entity_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

# Health Check Schema
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    database: Dict[str, Any]
    services: Dict[str, Any]

# Update forward references
UserResponse.model_rebuild()
ClientResponse.model_rebuild()
ProjectResponse.model_rebuild()
TaskResponse.model_rebuild()
CommentResponse.model_rebuild()

# Export schemas
__all__ = [
    # Base schemas
    "BaseSchema",
    "PaginationSchema", 
    "PaginatedResponse",
    
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserLogin",
    "UserToken",
    
    # Client schemas
    "ClientBase",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    
    # Project schemas
    "ProjectBase", 
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    
    # Task schemas
    "TaskBase",
    "TaskCreate", 
    "TaskUpdate",
    "TaskResponse",
    
    # Comment schemas
    "CommentBase",
    "CommentCreate",
    "CommentUpdate", 
    "CommentResponse",
    
    # Search schemas
    "SearchParams",
    "ProjectSearchParams",
    "TaskSearchParams",
    
    # Statistics schemas
    "ProjectStatistics",
    "TaskStatistics", 
    "UserStatistics",
    "ClientStatistics",
    
    # Error schemas
    "ErrorDetail",
    "ErrorResponse", 
    "ValidationErrorResponse",
    
    # CRM schemas
    "CRMSyncRequest",
    "CRMSyncResponse",
    
    # Health check
    "HealthCheckResponse",
    
    # Enums
    "UserRoleSchema",
    "UserStatusSchema",
    "ProjectStatusSchema", 
    "ProjectPrioritySchema",
    "TaskStatusSchema",
    "TaskPrioritySchema",
    "ClientStatusSchema",
    "CommentTypeSchema"
]