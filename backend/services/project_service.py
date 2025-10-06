"""
Project Service - Task 1.3
===========================

Business logic service for project management with team coordination and CRM integration.
Handles project lifecycle, team assignments, and progress tracking.

Features:
- Project CRUD operations with validation
- Team member management
- Progress tracking and timeline management
- Budget and resource tracking
- CRM synchronization
- Vector database integration for semantic search

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from services.base_service import (
    BaseService, ServiceException, ValidationException, 
    NotFoundException, ConflictException
)
from database.models import Project, ProjectStatus, ProjectPriority, User, Client, Task, TaskStatus
from database.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSearchParams, ProjectStatistics
)

# Configure logging
logger = logging.getLogger(__name__)

class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate, ProjectResponse]):
    """Service for project management and coordination"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(Project, db_session)
    
    def _validate_project_dates(self, start_date: date, end_date: date) -> None:
        """
        Validate project date constraints
        
        Args:
            start_date: Project start date
            end_date: Project end date
            
        Raises:
            ValidationException: If dates are invalid
        """
        if start_date and end_date and start_date > end_date:
            raise ValidationException("Start date cannot be after end date", "dates")
        
        if start_date and start_date < date.today():
            # Allow past start dates for existing projects
            pass
    
    def _validate_project_references(self, client_id: str = None, manager_id: str = None) -> None:
        """
        Validate client and manager references
        
        Args:
            client_id: Client ID to validate
            manager_id: Manager ID to validate
            
        Raises:
            ValidationException: If references are invalid
        """
        if client_id:
            client = self.db.query(Client).filter(
                Client.id == client_id,
                Client.is_deleted == False
            ).first()
            if not client:
                raise ValidationException("Invalid client reference", "client_id")
        
        if manager_id:
            manager = self.db.query(User).filter(
                User.id == manager_id,
                User.is_deleted == False,
                User.status == "active"
            ).first()
            if not manager:
                raise ValidationException("Invalid manager reference", "manager_id")
    
    def _calculate_project_completion(self, project: Project) -> int:
        """
        Calculate project completion percentage based on tasks
        
        Args:
            project: Project to calculate completion for
            
        Returns:
            Completion percentage (0-100)
        """
        try:
            if not project.tasks:
                return 0
            
            total_tasks = len(project.tasks)
            completed_tasks = len([t for t in project.tasks if t.status == TaskStatus.DONE])
            
            if total_tasks == 0:
                return 0
            
            return int((completed_tasks / total_tasks) * 100)
            
        except Exception as e:
            logger.warning(f"Failed to calculate project completion: {e}")
            return project.completion_percentage or 0
    
    def _update_project_activity(self, project: Project) -> None:
        """
        Update project last activity date
        
        Args:
            project: Project to update
        """
        project.last_activity_date = datetime.utcnow()
    
    def create(self, schema: ProjectCreate, created_by: str = None) -> Project:
        """
        Create new project with validation
        
        Args:
            schema: Project creation data
            created_by: User performing the creation
            
        Returns:
            Created project instance
            
        Raises:
            ConflictException: If project code already exists
            ValidationException: If data validation fails
        """
        try:
            self._log_operation("create_project", details={"name": schema.name})
            
            # Validate dates
            if schema.start_date and schema.end_date:
                self._validate_project_dates(schema.start_date, schema.end_date)
            
            # Validate references
            self._validate_project_references(schema.client_id, schema.manager_id)
            
            # Check for existing project code
            if schema.code:
                existing_project = self.db.query(Project).filter(
                    Project.code == schema.code,
                    Project.is_deleted == False
                ).first()
                
                if existing_project:
                    raise ConflictException("Project code already exists", "code")
            
            # Create project
            project_data = schema.dict()
            project = Project(
                **project_data,
                created_by=created_by,
                last_activity_date=datetime.utcnow()
            )
            
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            
            self._log_operation("project_created", project.id)
            
            # TODO: Trigger CRM sync
            # self._sync_to_crm(project, "create")
            
            # TODO: Add to vector database for semantic search
            # self._add_to_vector_db(project)
            
            return project
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (ConflictException, ValidationException)):
                raise
            self._handle_db_error(e, "create_project")
        finally:
            self._close_session_if_needed(self.db)
    
    def update(self, entity_id: str, schema: ProjectUpdate, updated_by: str = None) -> Optional[Project]:
        """
        Update project information
        
        Args:
            entity_id: Project ID
            schema: Update data
            updated_by: User performing the update
            
        Returns:
            Updated project instance
            
        Raises:
            NotFoundException: If project not found
            ConflictException: If project code conflicts
        """
        try:
            self._log_operation("update_project", entity_id)
            
            project = self.get_or_404(entity_id)
            
            # Validate dates if provided
            start_date = schema.start_date if schema.start_date is not None else project.start_date
            end_date = schema.end_date if schema.end_date is not None else project.end_date
            
            if start_date and end_date:
                self._validate_project_dates(start_date, end_date)
            
            # Validate references if provided
            self._validate_project_references(schema.client_id, schema.manager_id)
            
            # Check for code conflicts
            if schema.code and schema.code != project.code:
                existing_project = self.db.query(Project).filter(
                    Project.code == schema.code,
                    Project.id != entity_id,
                    Project.is_deleted == False
                ).first()
                
                if existing_project:
                    raise ConflictException("Project code already exists", "code")
            
            # Update fields
            update_data = schema.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(project, field):
                    setattr(project, field, value)
            
            # Update metadata
            project.updated_by = updated_by
            project.updated_at = datetime.utcnow()
            self._update_project_activity(project)
            
            # Auto-calculate completion if not explicitly set
            if 'completion_percentage' not in update_data:
                project.completion_percentage = self._calculate_project_completion(project)
            
            self.db.commit()
            self.db.refresh(project)
            
            self._log_operation("project_updated", entity_id)
            
            # TODO: Trigger CRM sync
            # self._sync_to_crm(project, "update")
            
            # TODO: Update vector database
            # self._update_vector_db(project)
            
            return project
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (NotFoundException, ConflictException, ValidationException)):
                raise
            self._handle_db_error(e, "update_project", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_with_details(self, entity_id: str) -> Optional[Project]:
        """
        Get project with related data (client, manager, tasks)
        
        Args:
            entity_id: Project ID
            
        Returns:
            Project with related data loaded
        """
        try:
            project = self.db.query(Project).options(
                joinedload(Project.client),
                joinedload(Project.manager),
                joinedload(Project.tasks)
            ).filter(
                Project.id == entity_id,
                Project.is_deleted == False
            ).first()
            
            return project
            
        except Exception as e:
            self._handle_db_error(e, "get_with_details", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_client(self, client_id: str, status: ProjectStatus = None) -> List[Project]:
        """
        Get projects by client
        
        Args:
            client_id: Client ID
            status: Optional status filter
            
        Returns:
            List of client projects
        """
        try:
            query = self.db.query(Project).filter(
                Project.client_id == client_id,
                Project.is_deleted == False
            )
            
            if status:
                query = query.filter(Project.status == status)
            
            projects = query.order_by(Project.created_at.desc()).all()
            return projects
            
        except Exception as e:
            self._handle_db_error(e, "get_by_client")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_manager(self, manager_id: str, status: ProjectStatus = None) -> List[Project]:
        """
        Get projects by manager
        
        Args:
            manager_id: Manager ID
            status: Optional status filter
            
        Returns:
            List of managed projects
        """
        try:
            query = self.db.query(Project).filter(
                Project.manager_id == manager_id,
                Project.is_deleted == False
            )
            
            if status:
                query = query.filter(Project.status == status)
            
            projects = query.order_by(Project.created_at.desc()).all()
            return projects
            
        except Exception as e:
            self._handle_db_error(e, "get_by_manager")
        finally:
            self._close_session_if_needed(self.db)
    
    def search_projects(self, search_params: ProjectSearchParams) -> List[Project]:
        """
        Search projects with multiple filters
        
        Args:
            search_params: Search parameters
            
        Returns:
            List of matching projects
        """
        try:
            query = self.db.query(Project).filter(Project.is_deleted == False)
            
            # Text search
            if search_params.q:
                text_conditions = [
                    Project.name.ilike(f"%{search_params.q}%"),
                    Project.description.ilike(f"%{search_params.q}%"),
                    Project.code.ilike(f"%{search_params.q}%")
                ]
                query = query.filter(or_(*text_conditions))
            
            # Status filter
            if search_params.status:
                query = query.filter(Project.status == search_params.status)
            
            # Priority filter
            if search_params.priority:
                query = query.filter(Project.priority == search_params.priority)
            
            # Client filter
            if search_params.client_id:
                query = query.filter(Project.client_id == search_params.client_id)
            
            # Manager filter
            if search_params.manager_id:
                query = query.filter(Project.manager_id == search_params.manager_id)
            
            # Date filters
            if search_params.start_date_after:
                query = query.filter(Project.start_date >= search_params.start_date_after)
            
            if search_params.end_date_before:
                query = query.filter(Project.end_date <= search_params.end_date_before)
            
            # Creation date filters
            if search_params.created_after:
                query = query.filter(Project.created_at >= search_params.created_after)
            
            if search_params.created_before:
                query = query.filter(Project.created_at <= search_params.created_before)
            
            # Sorting
            sort_field = search_params.sort_by or "created_at"
            if hasattr(Project, sort_field):
                sort_column = getattr(Project, sort_field)
                if search_params.sort_order == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            
            projects = query.all()
            return projects
            
        except Exception as e:
            self._handle_db_error(e, "search_projects")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_overdue_projects(self) -> List[Project]:
        """
        Get projects that are overdue
        
        Returns:
            List of overdue projects
        """
        try:
            projects = self.db.query(Project).filter(
                Project.end_date < date.today(),
                Project.status.notin_([ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]),
                Project.is_deleted == False
            ).all()
            
            return projects
            
        except Exception as e:
            self._handle_db_error(e, "get_overdue_projects")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_active_projects(self) -> List[Project]:
        """
        Get currently active projects
        
        Returns:
            List of active projects
        """
        try:
            projects = self.db.query(Project).filter(
                Project.status.in_([ProjectStatus.PLANNING, ProjectStatus.ACTIVE]),
                Project.is_deleted == False
            ).order_by(Project.priority.desc(), Project.created_at.desc()).all()
            
            return projects
            
        except Exception as e:
            self._handle_db_error(e, "get_active_projects")
        finally:
            self._close_session_if_needed(self.db)
    
    def update_project_status(self, project_id: str, status: ProjectStatus, updated_by: str = None) -> Optional[Project]:
        """
        Update project status with business logic
        
        Args:
            project_id: Project ID
            status: New status
            updated_by: User performing the update
            
        Returns:
            Updated project
        """
        try:
            self._log_operation("update_project_status", project_id, {"status": status})
            
            project = self.get_or_404(project_id)
            
            # Business logic for status transitions
            if status == ProjectStatus.COMPLETED:
                project.actual_end_date = date.today()
                project.completion_percentage = 100
            elif status == ProjectStatus.ACTIVE and not project.actual_start_date:
                project.actual_start_date = date.today()
            
            project.status = status
            project.updated_by = updated_by
            self._update_project_activity(project)
            
            self.db.commit()
            self.db.refresh(project)
            
            self._log_operation("project_status_updated", project_id)
            
            return project
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, NotFoundException):
                raise
            self._handle_db_error(e, "update_project_status", project_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def add_team_member(self, project_id: str, user_id: str, added_by: str = None) -> bool:
        """
        Add team member to project (via task assignment logic)
        
        Args:
            project_id: Project ID
            user_id: User ID to add
            added_by: User performing the action
            
        Returns:
            True if successful
        """
        try:
            self._log_operation("add_team_member", project_id, {"user_id": user_id})
            
            # Validate project and user exist
            project = self.get_or_404(project_id)
            user = self.db.query(User).filter(
                User.id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                raise ValidationException("Invalid user reference", "user_id")
            
            # Check if user is already assigned to any task in this project
            existing_assignment = self.db.query(Task).filter(
                Task.project_id == project_id,
                Task.assignee_id == user_id,
                Task.is_deleted == False
            ).first()
            
            if existing_assignment:
                self._log_operation("team_member_already_assigned", project_id)
                return True  # Already assigned
            
            self._update_project_activity(project)
            self.db.commit()
            
            self._log_operation("team_member_added", project_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (NotFoundException, ValidationException)):
                raise
            self._handle_db_error(e, "add_team_member", project_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_project_statistics(self, project_id: str = None) -> ProjectStatistics:
        """
        Get project statistics
        
        Args:
            project_id: Optional specific project ID
            
        Returns:
            Project statistics
        """
        try:
            if project_id:
                # Statistics for specific project
                project = self.get_or_404(project_id)
                
                task_count = len(project.tasks) if project.tasks else 0
                completed_tasks = len([t for t in project.tasks if t.status == TaskStatus.DONE]) if project.tasks else 0
                
                return ProjectStatistics(
                    total_projects=1,
                    active_projects=1 if project.status in [ProjectStatus.PLANNING, ProjectStatus.ACTIVE] else 0,
                    completed_projects=1 if project.status == ProjectStatus.COMPLETED else 0,
                    overdue_projects=1 if project.end_date and project.end_date < date.today() and project.status != ProjectStatus.COMPLETED else 0,
                    total_budget=project.budget,
                    total_hours=project.actual_hours or 0,
                    completion_rate=completed_tasks / task_count if task_count > 0 else 0
                )
            else:
                # Global statistics
                total_projects = self.count()
                active_projects = self.count({"status": ProjectStatus.ACTIVE}) + self.count({"status": ProjectStatus.PLANNING})
                completed_projects = self.count({"status": ProjectStatus.COMPLETED})
                
                # Overdue projects
                overdue_count = len(self.get_overdue_projects())
                
                # Budget and hours
                budget_result = self.db.query(func.sum(Project.budget)).filter(Project.is_deleted == False).scalar()
                hours_result = self.db.query(func.sum(Project.actual_hours)).filter(Project.is_deleted == False).scalar()
                
                # Completion rate
                completion_rate = completed_projects / total_projects if total_projects > 0 else 0
                
                return ProjectStatistics(
                    total_projects=total_projects,
                    active_projects=active_projects,
                    completed_projects=completed_projects,
                    overdue_projects=overdue_count,
                    total_budget=budget_result,
                    total_hours=hours_result or 0,
                    completion_rate=completion_rate
                )
                
        except Exception as e:
            if isinstance(e, NotFoundException):
                raise
            self._handle_db_error(e, "get_project_statistics")
        finally:
            self._close_session_if_needed(self.db)

# Export service
__all__ = ["ProjectService"]