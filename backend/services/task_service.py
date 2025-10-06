"""
Task Service - Task 1.3
========================

Business logic service for task management with dependencies, assignments, and progress tracking.
Handles task lifecycle, dependency management, and team coordination.

Features:
- Task CRUD operations with validation
- Task dependencies and subtask management
- Assignment and progress tracking
- Status workflow management
- CRM synchronization
- Time tracking and estimation

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text

from services.base_service import (
    BaseService, ServiceException, ValidationException, 
    NotFoundException, ConflictException
)
from database.models import (
    Task, TaskStatus, TaskPriority, Project, User, task_dependencies
)
from database.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskSearchParams, TaskStatistics
)

# Configure logging
logger = logging.getLogger(__name__)

class TaskDependencyException(ServiceException):
    """Exception for task dependency violations"""
    def __init__(self, message: str, circular_tasks: List[str] = None):
        super().__init__(message, "DEPENDENCY_ERROR")
        self.circular_tasks = circular_tasks or []

class TaskService(BaseService[Task, TaskCreate, TaskUpdate, TaskResponse]):
    """Service for task management and coordination"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(Task, db_session)
    
    def _validate_task_references(self, project_id: str, assignee_id: str = None, parent_task_id: str = None) -> None:
        """
        Validate project and user references
        
        Args:
            project_id: Project ID to validate
            assignee_id: Assignee ID to validate
            parent_task_id: Parent task ID to validate
            
        Raises:
            ValidationException: If references are invalid
        """
        # Validate project exists
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_deleted == False
        ).first()
        if not project:
            raise ValidationException("Invalid project reference", "project_id")
        
        # Validate assignee if provided
        if assignee_id:
            assignee = self.db.query(User).filter(
                User.id == assignee_id,
                User.is_deleted == False,
                User.status == "active"
            ).first()
            if not assignee:
                raise ValidationException("Invalid assignee reference", "assignee_id")
        
        # Validate parent task if provided
        if parent_task_id:
            parent_task = self.db.query(Task).filter(
                Task.id == parent_task_id,
                Task.project_id == project_id,  # Must be in same project
                Task.is_deleted == False
            ).first()
            if not parent_task:
                raise ValidationException("Invalid parent task reference", "parent_task_id")
    
    def _validate_task_dates(self, start_date: datetime, due_date: datetime) -> None:
        """
        Validate task date constraints
        
        Args:
            start_date: Task start date
            due_date: Task due date
            
        Raises:
            ValidationException: If dates are invalid
        """
        if start_date and due_date and start_date > due_date:
            raise ValidationException("Start date cannot be after due date", "dates")
    
    def _check_circular_dependency(self, task_id: str, depends_on_task_id: str) -> bool:
        """
        Check for circular dependencies in task relationships
        
        Args:
            task_id: Task that will depend on another
            depends_on_task_id: Task to depend on
            
        Returns:
            True if circular dependency would be created
        """
        visited = set()
        
        def has_path(from_id: str, to_id: str) -> bool:
            if from_id == to_id:
                return True
            
            if from_id in visited:
                return False
            
            visited.add(from_id)
            
            # Check direct dependencies
            dependencies = self.db.query(task_dependencies).filter(
                task_dependencies.c.task_id == from_id
            ).all()
            
            for dep in dependencies:
                if has_path(dep.depends_on_task_id, to_id):
                    return True
            
            return False
        
        # Check if depends_on_task has a path back to task
        return has_path(depends_on_task_id, task_id)
    
    def _update_task_completion(self, task: Task) -> None:
        """
        Update task completion logic
        
        Args:
            task: Task to update
        """
        if task.status == TaskStatus.DONE:
            task.completion_percentage = 100
            if not task.completed_date:
                task.completed_date = datetime.utcnow()
        elif task.status == TaskStatus.CANCELLED:
            # Keep existing completion percentage for cancelled tasks
            pass
        else:
            # Reset completed_date for non-done tasks
            task.completed_date = None
    
    def _can_start_task(self, task: Task) -> bool:
        """
        Check if task can be started based on dependencies
        
        Args:
            task: Task to check
            
        Returns:
            True if task can be started
        """
        # Check if all dependency tasks are completed
        if task.dependencies:
            for dependency in task.dependencies:
                if dependency.status != TaskStatus.DONE:
                    return False
        
        return True
    
    def create(self, schema: TaskCreate, created_by: str = None) -> Task:
        """
        Create new task with validation
        
        Args:
            schema: Task creation data
            created_by: User performing the creation
            
        Returns:
            Created task instance
            
        Raises:
            ValidationException: If data validation fails
        """
        try:
            self._log_operation("create_task", details={"title": schema.title})
            
            # Validate references
            self._validate_task_references(schema.project_id, schema.assignee_id, schema.parent_task_id)
            
            # Validate dates
            if schema.start_date and schema.due_date:
                self._validate_task_dates(schema.start_date, schema.due_date)
            
            # Create task
            task_data = schema.dict()
            task = Task(
                **task_data,
                created_by=created_by
            )
            
            # Update completion logic
            self._update_task_completion(task)
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            self._log_operation("task_created", task.id)
            
            # TODO: Trigger CRM sync
            # self._sync_to_crm(task, "create")
            
            # TODO: Add to vector database for semantic search
            # self._add_to_vector_db(task)
            
            return task
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ValidationException):
                raise
            self._handle_db_error(e, "create_task")
        finally:
            self._close_session_if_needed(self.db)
    
    def update(self, entity_id: str, schema: TaskUpdate, updated_by: str = None) -> Optional[Task]:
        """
        Update task information
        
        Args:
            entity_id: Task ID
            schema: Update data
            updated_by: User performing the update
            
        Returns:
            Updated task instance
            
        Raises:
            NotFoundException: If task not found
            ValidationException: If validation fails
        """
        try:
            self._log_operation("update_task", entity_id)
            
            task = self.get_or_404(entity_id)
            
            # Validate references if provided
            if schema.assignee_id is not None or schema.parent_task_id is not None:
                self._validate_task_references(
                    task.project_id,
                    schema.assignee_id,
                    schema.parent_task_id
                )
            
            # Validate dates if provided
            start_date = schema.start_date if schema.start_date is not None else task.start_date
            due_date = schema.due_date if schema.due_date is not None else task.due_date
            
            if start_date and due_date:
                self._validate_task_dates(start_date, due_date)
            
            # Update fields
            update_data = schema.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(task, field):
                    setattr(task, field, value)
            
            # Update metadata
            task.updated_by = updated_by
            task.updated_at = datetime.utcnow()
            
            # Update completion logic
            self._update_task_completion(task)
            
            self.db.commit()
            self.db.refresh(task)
            
            self._log_operation("task_updated", entity_id)
            
            # TODO: Trigger CRM sync
            # self._sync_to_crm(task, "update")
            
            # TODO: Update vector database
            # self._update_vector_db(task)
            
            return task
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (NotFoundException, ValidationException)):
                raise
            self._handle_db_error(e, "update_task", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_with_details(self, entity_id: str) -> Optional[Task]:
        """
        Get task with related data (project, assignee, dependencies)
        
        Args:
            entity_id: Task ID
            
        Returns:
            Task with related data loaded
        """
        try:
            task = self.db.query(Task).options(
                joinedload(Task.project),
                joinedload(Task.assignee),
                joinedload(Task.parent_task),
                joinedload(Task.subtasks),
                joinedload(Task.dependencies),
                joinedload(Task.dependent_tasks)
            ).filter(
                Task.id == entity_id,
                Task.is_deleted == False
            ).first()
            
            return task
            
        except Exception as e:
            self._handle_db_error(e, "get_with_details", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_project(self, project_id: str, status: TaskStatus = None) -> List[Task]:
        """
        Get tasks by project
        
        Args:
            project_id: Project ID
            status: Optional status filter
            
        Returns:
            List of project tasks
        """
        try:
            query = self.db.query(Task).filter(
                Task.project_id == project_id,
                Task.is_deleted == False
            )
            
            if status:
                query = query.filter(Task.status == status)
            
            tasks = query.order_by(Task.created_at.desc()).all()
            return tasks
            
        except Exception as e:
            self._handle_db_error(e, "get_by_project")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_assignee(self, assignee_id: str, status: TaskStatus = None) -> List[Task]:
        """
        Get tasks by assignee
        
        Args:
            assignee_id: Assignee ID
            status: Optional status filter
            
        Returns:
            List of assigned tasks
        """
        try:
            query = self.db.query(Task).filter(
                Task.assignee_id == assignee_id,
                Task.is_deleted == False
            )
            
            if status:
                query = query.filter(Task.status == status)
            
            tasks = query.order_by(Task.due_date.asc()).all()
            return tasks
            
        except Exception as e:
            self._handle_db_error(e, "get_by_assignee")
        finally:
            self._close_session_if_needed(self.db)
    
    def search_tasks(self, search_params: TaskSearchParams) -> List[Task]:
        """
        Search tasks with multiple filters
        
        Args:
            search_params: Search parameters
            
        Returns:
            List of matching tasks
        """
        try:
            query = self.db.query(Task).filter(Task.is_deleted == False)
            
            # Text search
            if search_params.q:
                text_conditions = [
                    Task.title.ilike(f"%{search_params.q}%"),
                    Task.description.ilike(f"%{search_params.q}%")
                ]
                query = query.filter(or_(*text_conditions))
            
            # Status filter
            if search_params.status:
                query = query.filter(Task.status == search_params.status)
            
            # Priority filter
            if search_params.priority:
                query = query.filter(Task.priority == search_params.priority)
            
            # Project filter
            if search_params.project_id:
                query = query.filter(Task.project_id == search_params.project_id)
            
            # Assignee filter
            if search_params.assignee_id:
                query = query.filter(Task.assignee_id == search_params.assignee_id)
            
            # Due date filter
            if search_params.due_date_before:
                query = query.filter(Task.due_date <= search_params.due_date_before)
            
            # Tags filter
            if search_params.tags:
                for tag in search_params.tags:
                    query = query.filter(Task.tags.contains([tag]))
            
            # Labels filter
            if search_params.labels:
                for label in search_params.labels:
                    query = query.filter(Task.labels.contains([label]))
            
            # Creation date filters
            if search_params.created_after:
                query = query.filter(Task.created_at >= search_params.created_after)
            
            if search_params.created_before:
                query = query.filter(Task.created_at <= search_params.created_before)
            
            # Sorting
            sort_field = search_params.sort_by or "created_at"
            if hasattr(Task, sort_field):
                sort_column = getattr(Task, sort_field)
                if search_params.sort_order == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            
            tasks = query.all()
            return tasks
            
        except Exception as e:
            self._handle_db_error(e, "search_tasks")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_overdue_tasks(self) -> List[Task]:
        """
        Get tasks that are overdue
        
        Returns:
            List of overdue tasks
        """
        try:
            tasks = self.db.query(Task).filter(
                Task.due_date < datetime.utcnow(),
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
                Task.is_deleted == False
            ).order_by(Task.due_date.asc()).all()
            
            return tasks
            
        except Exception as e:
            self._handle_db_error(e, "get_overdue_tasks")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_blocked_tasks(self) -> List[Task]:
        """
        Get tasks that are blocked
        
        Returns:
            List of blocked tasks
        """
        try:
            tasks = self.db.query(Task).filter(
                Task.status == TaskStatus.BLOCKED,
                Task.is_deleted == False
            ).order_by(Task.created_at.desc()).all()
            
            return tasks
            
        except Exception as e:
            self._handle_db_error(e, "get_blocked_tasks")
        finally:
            self._close_session_if_needed(self.db)
    
    def update_task_status(self, task_id: str, status: TaskStatus, updated_by: str = None) -> Optional[Task]:
        """
        Update task status with business logic
        
        Args:
            task_id: Task ID
            status: New status
            updated_by: User performing the update
            
        Returns:
            Updated task
            
        Raises:
            ValidationException: If status transition is invalid
        """
        try:
            self._log_operation("update_task_status", task_id, {"status": status})
            
            task = self.get_or_404(task_id)
            
            # Validate status transition
            if status == TaskStatus.IN_PROGRESS:
                if not self._can_start_task(task):
                    raise ValidationException("Cannot start task with incomplete dependencies")
                
                if not task.start_date:
                    task.start_date = datetime.utcnow()
            
            task.status = status
            task.updated_by = updated_by
            
            # Update completion logic
            self._update_task_completion(task)
            
            self.db.commit()
            self.db.refresh(task)
            
            self._log_operation("task_status_updated", task_id)
            
            return task
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (NotFoundException, ValidationException)):
                raise
            self._handle_db_error(e, "update_task_status", task_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def add_dependency(self, task_id: str, depends_on_task_id: str, added_by: str = None) -> bool:
        """
        Add task dependency
        
        Args:
            task_id: Task that will depend on another
            depends_on_task_id: Task to depend on
            added_by: User performing the action
            
        Returns:
            True if dependency added successfully
            
        Raises:
            TaskDependencyException: If circular dependency detected
            ValidationException: If tasks are invalid
        """
        try:
            self._log_operation("add_dependency", task_id, {"depends_on": depends_on_task_id})
            
            # Validate both tasks exist and are in same project
            task = self.get_or_404(task_id)
            depends_on_task = self.get_or_404(depends_on_task_id)
            
            if task.project_id != depends_on_task.project_id:
                raise ValidationException("Tasks must be in the same project")
            
            # Check for circular dependency
            if self._check_circular_dependency(task_id, depends_on_task_id):
                raise TaskDependencyException("Circular dependency detected")
            
            # Check if dependency already exists
            existing = self.db.query(task_dependencies).filter(
                task_dependencies.c.task_id == task_id,
                task_dependencies.c.depends_on_task_id == depends_on_task_id
            ).first()
            
            if existing:
                return True  # Already exists
            
            # Add dependency
            stmt = task_dependencies.insert().values(
                task_id=task_id,
                depends_on_task_id=depends_on_task_id,
                created_at=datetime.utcnow(),
                created_by=added_by
            )
            self.db.execute(stmt)
            self.db.commit()
            
            self._log_operation("dependency_added", task_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (NotFoundException, ValidationException, TaskDependencyException)):
                raise
            self._handle_db_error(e, "add_dependency", task_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def remove_dependency(self, task_id: str, depends_on_task_id: str) -> bool:
        """
        Remove task dependency
        
        Args:
            task_id: Task ID
            depends_on_task_id: Dependency task ID
            
        Returns:
            True if dependency removed successfully
        """
        try:
            self._log_operation("remove_dependency", task_id, {"depends_on": depends_on_task_id})
            
            # Remove dependency
            stmt = task_dependencies.delete().where(
                and_(
                    task_dependencies.c.task_id == task_id,
                    task_dependencies.c.depends_on_task_id == depends_on_task_id
                )
            )
            result = self.db.execute(stmt)
            self.db.commit()
            
            success = result.rowcount > 0
            if success:
                self._log_operation("dependency_removed", task_id)
            
            return success
            
        except Exception as e:
            self.db.rollback()
            self._handle_db_error(e, "remove_dependency", task_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def assign_task(self, task_id: str, assignee_id: str, assigned_by: str = None) -> Optional[Task]:
        """
        Assign task to user
        
        Args:
            task_id: Task ID
            assignee_id: User ID to assign to
            assigned_by: User performing the assignment
            
        Returns:
            Updated task
        """
        try:
            self._log_operation("assign_task", task_id, {"assignee_id": assignee_id})
            
            task = self.get_or_404(task_id)
            
            # Validate assignee
            if assignee_id:
                assignee = self.db.query(User).filter(
                    User.id == assignee_id,
                    User.is_deleted == False,
                    User.status == "active"
                ).first()
                if not assignee:
                    raise ValidationException("Invalid assignee reference", "assignee_id")
            
            task.assignee_id = assignee_id
            task.updated_by = assigned_by
            
            self.db.commit()
            self.db.refresh(task)
            
            self._log_operation("task_assigned", task_id)
            return task
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (NotFoundException, ValidationException)):
                raise
            self._handle_db_error(e, "assign_task", task_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def log_time(self, task_id: str, hours: Decimal, logged_by: str = None) -> Optional[Task]:
        """
        Log time spent on task
        
        Args:
            task_id: Task ID
            hours: Hours to log
            logged_by: User logging the time
            
        Returns:
            Updated task
        """
        try:
            self._log_operation("log_time", task_id, {"hours": float(hours)})
            
            task = self.get_or_404(task_id)
            
            task.actual_hours = (task.actual_hours or Decimal(0)) + hours
            task.updated_by = logged_by
            
            self.db.commit()
            self.db.refresh(task)
            
            self._log_operation("time_logged", task_id)
            return task
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, NotFoundException):
                raise
            self._handle_db_error(e, "log_time", task_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_task_statistics(self, project_id: str = None) -> TaskStatistics:
        """
        Get task statistics
        
        Args:
            project_id: Optional specific project ID
            
        Returns:
            Task statistics
        """
        try:
            base_query = self.db.query(Task).filter(Task.is_deleted == False)
            
            if project_id:
                base_query = base_query.filter(Task.project_id == project_id)
            
            total_tasks = base_query.count()
            completed_tasks = base_query.filter(Task.status == TaskStatus.DONE).count()
            overdue_tasks = base_query.filter(
                Task.due_date < datetime.utcnow(),
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED])
            ).count()
            blocked_tasks = base_query.filter(Task.status == TaskStatus.BLOCKED).count()
            
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            # Calculate average completion time for completed tasks
            completed_with_dates = base_query.filter(
                Task.status == TaskStatus.DONE,
                Task.completed_date.isnot(None),
                Task.start_date.isnot(None)
            ).all()
            
            if completed_with_dates:
                total_days = sum([
                    (task.completed_date - task.start_date).days
                    for task in completed_with_dates
                    if task.completed_date and task.start_date
                ])
                average_completion_time = total_days / len(completed_with_dates)
            else:
                average_completion_time = None
            
            return TaskStatistics(
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                overdue_tasks=overdue_tasks,
                blocked_tasks=blocked_tasks,
                completion_rate=completion_rate,
                average_completion_time=average_completion_time
            )
            
        except Exception as e:
            self._handle_db_error(e, "get_task_statistics")
        finally:
            self._close_session_if_needed(self.db)

# Export service
__all__ = ["TaskService", "TaskDependencyException"]