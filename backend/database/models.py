"""
Database Models - Task 1.3
===========================

SQLAlchemy ORM models for AI Coordination Agent backend.
Comprehensive database schema with relationships and integration with Task 1.1 vector database.

Models:
- User: User authentication and profile management
- Client: Client/customer information and relationships  
- Project: Project management with team assignments
- Task: Task tracking with dependencies and assignments
- Comment: AI-generated comments and human feedback
- CRMSync: CRM synchronization tracking

Features:
- Full relationship mapping between entities
- Vector database integration for semantic search
- CRM synchronization tracking
- Audit trails and timestamps
- Flexible metadata support

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, JSON, 
    ForeignKey, Enum, Date, Index, UniqueConstraint,
    event, text
)
from sqlalchemy.types import DECIMAL
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
import enum

from database.connection import Base

# Enums for status fields
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    CLIENT = "client"
    VIEWER = "viewer"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class ProjectPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ClientStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    FORMER = "former"

class CommentType(str, enum.Enum):
    AI_GENERATED = "ai_generated"
    HUMAN_FEEDBACK = "human_feedback"
    SYSTEM = "system"
    NOTIFICATION = "notification"

class CRMSyncStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"

# Base model with common fields
class BaseModel(Base):
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    extra_data = Column(JSON, default=dict, nullable=True)  # Renamed from metadata to avoid SQLAlchemy conflict
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

# User Model
class User(BaseModel):
    __tablename__ = "users"
    
    # Authentication fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=True)
    
    # Profile fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Role and status
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    
    # Authentication tracking
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Preferences and settings
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    preferences = Column(JSON, default=dict, nullable=True)
    
    # CRM integration
    crm_user_id = Column(String(100), nullable=True, index=True)
    external_ids = Column(JSON, default=dict, nullable=True)
    
    # Relationships
    managed_projects = relationship("Project", foreign_keys="Project.manager_id", back_populates="manager")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    comments = relationship("Comment", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email_status', 'email', 'status'),
        Index('idx_user_role_status', 'role', 'status'),
        Index('idx_user_crm_id', 'crm_user_id'),
    )
    
    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @hybrid_property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and not self.is_deleted
    
    @hybrid_property
    def is_locked(self) -> bool:
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

# Client Model
class Client(BaseModel):
    __tablename__ = "clients"
    
    # Basic information
    name = Column(String(200), nullable=False, index=True)
    company = Column(String(200), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Business information
    industry = Column(String(100), nullable=True, index=True)
    company_size = Column(String(50), nullable=True)
    annual_revenue = Column(DECIMAL(15, 2), nullable=True)
    
    # Status and relationship
    status = Column(Enum(ClientStatus), default=ClientStatus.ACTIVE, nullable=False)
    acquisition_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    # CRM integration
    crm_client_id = Column(String(100), nullable=True, index=True)
    external_ids = Column(JSON, default=dict, nullable=True)
    
    # Vector search data
    vector_id = Column(String(100), nullable=True, index=True)
    search_keywords = Column(Text, nullable=True)
    
    # Relationships
    projects = relationship("Project", back_populates="client")
    
    # Indexes
    __table_args__ = (
        Index('idx_client_name_status', 'name', 'status'),
        Index('idx_client_company_status', 'company', 'status'),
        Index('idx_client_industry_status', 'industry', 'status'),
        Index('idx_client_crm_id', 'crm_client_id'),
    )
    
    @hybrid_property
    def project_count(self) -> int:
        return len(self.projects) if self.projects else 0
    
    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, company={self.company})>"

# Project Model
class Project(BaseModel):
    __tablename__ = "projects"
    
    # Basic information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(String(20), unique=True, nullable=True, index=True)
    
    # Status and priority
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING, nullable=False)
    priority = Column(Enum(ProjectPriority), default=ProjectPriority.MEDIUM, nullable=False)
    
    # Dates and timeline
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    
    # Budget and resources
    budget = Column(DECIMAL(15, 2), nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, default=0, nullable=False)
    
    # Team and relationships
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=True, index=True)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    # Progress tracking
    completion_percentage = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(DateTime, nullable=True)
    
    # CRM integration
    crm_project_id = Column(String(100), nullable=True, index=True)
    external_ids = Column(JSON, default=dict, nullable=True)
    
    # Vector search data
    vector_id = Column(String(100), nullable=True, index=True)
    search_keywords = Column(Text, nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="projects")
    manager = relationship("User", foreign_keys=[manager_id], back_populates="managed_projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="project")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_status_priority', 'status', 'priority'),
        Index('idx_project_client_status', 'client_id', 'status'),
        Index('idx_project_manager_status', 'manager_id', 'status'),
        Index('idx_project_dates', 'start_date', 'end_date'),
        Index('idx_project_crm_id', 'crm_project_id'),
    )
    
    @hybrid_property
    def is_active(self) -> bool:
        return self.status in [ProjectStatus.PLANNING, ProjectStatus.ACTIVE]
    
    @hybrid_property
    def is_overdue(self) -> bool:
        if not self.end_date:
            return False
        return self.end_date < date.today() and self.status != ProjectStatus.COMPLETED
    
    @hybrid_property
    def task_count(self) -> int:
        return len(self.tasks) if self.tasks else 0
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"

# Task Model
class Task(BaseModel):
    __tablename__ = "tasks"
    
    # Basic information
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Status and priority
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    
    # Relationships
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    assignee_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    parent_task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True, index=True)
    
    # Dates and timeline
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    # Effort estimation
    estimated_hours = Column(DECIMAL(5, 2), nullable=True)
    actual_hours = Column(DECIMAL(5, 2), default=0, nullable=False)
    
    # Progress and completion
    completion_percentage = Column(Integer, default=0, nullable=False)
    
    # Labels and categorization
    tags = Column(JSON, default=list, nullable=True)
    labels = Column(JSON, default=list, nullable=True)
    
    # CRM integration
    crm_task_id = Column(String(100), nullable=True, index=True)
    external_ids = Column(JSON, default=dict, nullable=True)
    
    # Vector search data
    vector_id = Column(String(100), nullable=True, index=True)
    search_keywords = Column(Text, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    creator = relationship("User", foreign_keys=[BaseModel.created_by], back_populates="created_tasks")
    parent_task = relationship("Task", remote_side="Task.id", back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task")
    dependencies = relationship(
        "Task", 
        secondary="task_dependencies",
        primaryjoin="Task.id==task_dependencies.c.task_id",
        secondaryjoin="Task.id==task_dependencies.c.depends_on_task_id",
        back_populates="dependent_tasks"
    )
    dependent_tasks = relationship(
        "Task",
        secondary="task_dependencies", 
        primaryjoin="Task.id==task_dependencies.c.depends_on_task_id",
        secondaryjoin="Task.id==task_dependencies.c.task_id",
        back_populates="dependencies"
    )
    comments = relationship("Comment", back_populates="task")
    
    # Indexes
    __table_args__ = (
        Index('idx_task_status_priority', 'status', 'priority'),
        Index('idx_task_project_status', 'project_id', 'status'),
        Index('idx_task_assignee_status', 'assignee_id', 'status'),
        Index('idx_task_due_date', 'due_date'),
        Index('idx_task_parent', 'parent_task_id'),
        Index('idx_task_crm_id', 'crm_task_id'),
    )
    
    @hybrid_property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        return self.due_date < datetime.utcnow() and self.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]
    
    @hybrid_property
    def is_blocked(self) -> bool:
        return self.status == TaskStatus.BLOCKED
    
    @hybrid_property
    def subtask_count(self) -> int:
        return len(self.subtasks) if self.subtasks else 0
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"

# Task Dependencies Association Table
from sqlalchemy import Table
task_dependencies = Table(
    'task_dependencies',
    Base.metadata,
    Column('task_id', String(36), ForeignKey('tasks.id'), primary_key=True),
    Column('depends_on_task_id', String(36), ForeignKey('tasks.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('created_by', String(36), nullable=True)
)

# Comment Model (AI-generated comments and human feedback)
class Comment(BaseModel):
    __tablename__ = "comments"
    
    # Basic information
    content = Column(Text, nullable=False)
    comment_type = Column(Enum(CommentType), default=CommentType.AI_GENERATED, nullable=False)
    
    # Relationships
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True, index=True)
    
    # AI comment specific fields
    ai_model = Column(String(100), nullable=True)
    ai_confidence = Column(DECIMAL(5, 4), nullable=True)
    ai_context = Column(JSON, default=dict, nullable=True)
    
    # Human feedback fields
    is_helpful = Column(Boolean, nullable=True)
    feedback_score = Column(Integer, nullable=True)
    human_feedback = Column(Text, nullable=True)
    
    # Vector search data
    vector_id = Column(String(100), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="comments")
    project = relationship("Project", back_populates="comments")
    task = relationship("Task", back_populates="comments")
    
    # Indexes
    __table_args__ = (
        Index('idx_comment_type_created', 'comment_type', 'created_at'),
        Index('idx_comment_user_type', 'user_id', 'comment_type'),
        Index('idx_comment_project_type', 'project_id', 'comment_type'),
        Index('idx_comment_task_type', 'task_id', 'comment_type'),
    )
    
    def __repr__(self):
        return f"<Comment(id={self.id}, type={self.comment_type}, user_id={self.user_id})>"

# CRM Synchronization Model
class CRMSync(BaseModel):
    __tablename__ = "crm_sync"
    
    # Sync operation details
    entity_type = Column(String(50), nullable=False, index=True)  # user, client, project, task
    entity_id = Column(String(36), nullable=False, index=True)
    operation = Column(String(20), nullable=False)  # create, update, delete, sync
    
    # CRM details
    crm_system = Column(String(50), nullable=False)  # salesforce, hubspot, etc.
    crm_entity_id = Column(String(100), nullable=True)
    
    # Sync status
    status = Column(Enum(CRMSyncStatus), default=CRMSyncStatus.PENDING, nullable=False)
    sync_started_at = Column(DateTime, nullable=True)
    sync_completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime, nullable=True)
    
    # Sync data
    sync_data = Column(JSON, default=dict, nullable=True)
    response_data = Column(JSON, default=dict, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_crm_sync_entity', 'entity_type', 'entity_id'),
        Index('idx_crm_sync_status', 'status', 'sync_started_at'),
        Index('idx_crm_sync_retry', 'status', 'next_retry_at'),
        UniqueConstraint('entity_type', 'entity_id', 'crm_system', 'operation', name='uq_crm_sync_operation'),
    )
    
    def __repr__(self):
        return f"<CRMSync(id={self.id}, entity_type={self.entity_type}, status={self.status})>"

# Model registration and initialization
def register_models():
    """Register all models with the Base metadata"""
    # Import all models to ensure they're registered
    models = [User, Client, Project, Task, Comment, CRMSync]
    
    # Create indexes and constraints
    for model in models:
        if hasattr(model, '__table__'):
            # Ensure table is registered
            pass
    
    return models

# Event listeners for automatic updates
@event.listens_for(User, 'before_update')
def update_user_timestamp(mapper, connection, target):
    target.updated_at = datetime.utcnow()

@event.listens_for(Project, 'before_update')
def update_project_activity(mapper, connection, target):
    target.updated_at = datetime.utcnow()
    target.last_activity_date = datetime.utcnow()

@event.listens_for(Task, 'before_update')
def update_task_completion(mapper, connection, target):
    target.updated_at = datetime.utcnow()
    # Update completion date when status changes to DONE
    if target.status == TaskStatus.DONE and not target.completed_date:
        target.completed_date = datetime.utcnow()
        target.completion_percentage = 100

# Export models
__all__ = [
    "Base",
    "BaseModel", 
    "User",
    "Client", 
    "Project",
    "Task",
    "Comment",
    "CRMSync",
    "task_dependencies",
    "UserRole",
    "UserStatus", 
    "ProjectStatus",
    "ProjectPriority",
    "TaskStatus",
    "TaskPriority",
    "ClientStatus",
    "CommentType",
    "CRMSyncStatus",
    "register_models"
]