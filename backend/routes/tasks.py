"""
Tasks API Routes - Task 1.3
===========================

FastAPI routes for task management including:
- CRUD operations for tasks
- Task assignment and status updates
- Task dependencies and relationships
- Integration with CRM API
- Vector search capabilities

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
from database.models import Task as DBTask, Project as DBProject, User as DBUser
from schemas.task_schemas import (
    TaskCreate, TaskUpdate, TaskResponse, 
    TaskListResponse, TaskWithProject, TaskAssignment
)
from services.task_service import TaskService
from core.dependencies import get_current_user, get_crm_client
from core.pagination import PaginationParams, paginate
from core.exceptions import TaskNotFoundError, ValidationError, ProjectNotFoundError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/",
    response_model=TaskListResponse,
    summary="Get all tasks",
    description="Retrieve a paginated list of tasks with optional filtering"
)
async def get_tasks(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee ID"),
    reporter_id: Optional[int] = Query(None, description="Filter by reporter ID"),
    search: Optional[str] = Query(None, description="Search in task title/description"),
    due_date_from: Optional[str] = Query(None, description="Filter tasks due after this date"),
    due_date_to: Optional[str] = Query(None, description="Filter tasks due before this date"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all tasks with optional filtering and pagination.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 50, max: 100)
    - **status**: Filter by task status (todo, in_progress, review, done, cancelled)
    - **priority**: Filter by priority (low, medium, high, critical)
    - **project_id**: Filter by project ID
    - **assignee_id**: Filter by assignee ID
    - **reporter_id**: Filter by reporter ID
    - **search**: Search term for title/description
    - **due_date_from**: Filter tasks due after this date (YYYY-MM-DD)
    - **due_date_to**: Filter tasks due before this date (YYYY-MM-DD)
    """
    try:
        logger.info(f"Getting tasks for user {current_user.get('id')} with filters")
        
        service = TaskService(db)
        
        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if priority:
            filters['priority'] = priority
        if project_id:
            filters['project_id'] = project_id
        if assignee_id:
            filters['assignee_id'] = assignee_id
        if reporter_id:
            filters['reporter_id'] = reporter_id
        if search:
            filters['search'] = search
        if due_date_from:
            filters['due_date_from'] = due_date_from
        if due_date_to:
            filters['due_date_to'] = due_date_to
        
        tasks, total_count = service.get_tasks_paginated(
            page=pagination.page,
            size=pagination.size,
            filters=filters
        )
        
        return TaskListResponse(
            data=tasks,
            total=total_count,
            page=pagination.page,
            size=pagination.size,
            pages=(total_count + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tasks: {str(e)}"
        )

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Retrieve a specific task by its ID"
)
async def get_task(
    task_id: int = Path(..., description="Task ID"),
    include_project: bool = Query(False, description="Include project details"),
    include_dependencies: bool = Query(False, description="Include task dependencies"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific task by ID.
    
    - **task_id**: The ID of the task to retrieve
    - **include_project**: Whether to include project details in response
    - **include_dependencies**: Whether to include task dependencies
    """
    try:
        logger.info(f"Getting task {task_id} for user {current_user.get('id')}")
        
        service = TaskService(db)
        task = service.get_task_by_id(
            task_id, 
            include_project=include_project,
            include_dependencies=include_dependencies
        )
        
        if not task:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
        return TaskResponse(data=task)
        
    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task: {str(e)}"
        )

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new task",
    description="Create a new task"
)
async def create_task(
    task_data: TaskCreate,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Create a new task.
    
    - **title**: Task title (required)
    - **description**: Task description
    - **status**: Task status (default: todo)
    - **priority**: Priority level (default: medium)
    - **project_id**: Associated project ID (required)
    - **assignee_id**: Assigned user ID
    - **due_date**: Task due date
    - **estimated_hours**: Estimated work hours
    - **tags**: List of tags
    - **dependencies**: List of dependent task IDs
    """
    try:
        logger.info(f"Creating task '{task_data.title}' for user {current_user.get('id')}")
        
        service = TaskService(db)
        
        # Set reporter as current user if not specified
        if not task_data.reporter_id:
            task_data.reporter_id = current_user.get('id')
        
        # Validate project exists
        if task_data.project_id:
            project = service.get_project_by_id(task_data.project_id)
            if not project:
                raise ProjectNotFoundError(f"Project with ID {task_data.project_id} not found")
        
        # Create task in database
        task = service.create_task(task_data, creator_id=current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client:
            try:
                from crm_api_endpoints import Task as CRMTask
                crm_task = CRMTask(
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    priority=task.priority,
                    project_id=task.project.crm_id if task.project and task.project.crm_id else None,
                    assignee_id=task.assignee_id,
                    reporter_id=task.reporter_id,
                    due_date=task.due_date.isoformat() if task.due_date else None,
                    estimated_hours=float(task.estimated_hours) if task.estimated_hours else None,
                    tags=task.tags if task.tags else []
                )
                
                crm_response = crm_client.tasks.create(crm_task)
                service.update_crm_id(task.id, crm_response.id)
                logger.info(f"Task {task.id} synced to CRM with ID {crm_response.id}")
                
            except Exception as e:
                logger.warning(f"Failed to sync task to CRM: {e}")
        
        return TaskResponse(
            data=task,
            message="Task created successfully"
        )
        
    except (ValidationError, ProjectNotFoundError) as e:
        logger.warning(f"Validation error creating task: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )

@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update an existing task"
)
async def update_task(
    task_id: int = Path(..., description="Task ID"),
    task_data: TaskUpdate = ...,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Update an existing task.
    
    - **task_id**: The ID of the task to update
    - Only provided fields will be updated
    """
    try:
        logger.info(f"Updating task {task_id} for user {current_user.get('id')}")
        
        service = TaskService(db)
        
        # Check if task exists
        existing_task = service.get_task_by_id(task_id)
        if not existing_task:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
        # Update task
        task = service.update_task(task_id, task_data, updater_id=current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client and task.crm_id:
            try:
                from crm_api_endpoints import Task as CRMTask
                crm_task = CRMTask(
                    id=task.crm_id,
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    priority=task.priority,
                    project_id=task.project.crm_id if task.project and task.project.crm_id else None,
                    assignee_id=task.assignee_id,
                    reporter_id=task.reporter_id,
                    due_date=task.due_date.isoformat() if task.due_date else None,
                    estimated_hours=float(task.estimated_hours) if task.estimated_hours else None,
                    actual_hours=float(task.actual_hours) if task.actual_hours else None,
                    tags=task.tags if task.tags else []
                )
                
                crm_client.tasks.update(task.crm_id, crm_task)
                logger.info(f"Task {task.id} synced to CRM")
                
            except Exception as e:
                logger.warning(f"Failed to sync task update to CRM: {e}")
        
        return TaskResponse(
            data=task,
            message="Task updated successfully"
        )
        
    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Validation error updating task: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete a task"
)
async def delete_task(
    task_id: int = Path(..., description="Task ID"),
    sync_to_crm: bool = Query(True, description="Sync deletion to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Delete a task.
    
    - **task_id**: The ID of the task to delete
    """
    try:
        logger.info(f"Deleting task {task_id} for user {current_user.get('id')}")
        
        service = TaskService(db)
        
        # Check if task exists
        task = service.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
        # Delete from CRM first if needed
        if sync_to_crm and crm_client and task.crm_id:
            try:
                crm_client.tasks.delete(task.crm_id)
                logger.info(f"Task {task_id} deleted from CRM")
            except Exception as e:
                logger.warning(f"Failed to delete task from CRM: {e}")
        
        # Delete from database
        service.delete_task(task_id, deleter_id=current_user.get('id'))
        
        logger.info(f"Task {task_id} deleted successfully")
        
    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )

@router.patch(
    "/{task_id}/assign",
    response_model=TaskResponse,
    summary="Assign task",
    description="Assign task to a user"
)
async def assign_task(
    task_id: int = Path(..., description="Task ID"),
    assignment: TaskAssignment = ...,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Assign a task to a user.
    
    - **task_id**: The ID of the task to assign
    - **assignee_id**: The ID of the user to assign the task to
    """
    try:
        logger.info(f"Assigning task {task_id} to user {assignment.assignee_id}")
        
        service = TaskService(db)
        
        # Check if task exists
        task = service.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
        # Assign task
        updated_task = service.assign_task(task_id, assignment.assignee_id, current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client and updated_task.crm_id:
            try:
                crm_client.tasks.assign_task(updated_task.crm_id, assignment.assignee_id)
                logger.info(f"Task assignment synced to CRM")
            except Exception as e:
                logger.warning(f"Failed to sync task assignment to CRM: {e}")
        
        return TaskResponse(
            data=updated_task,
            message=f"Task assigned to user {assignment.assignee_id}"
        )
        
    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign task: {str(e)}"
        )

@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Update task status",
    description="Update the status of a task"
)
async def update_task_status(
    task_id: int = Path(..., description="Task ID"),
    status_update: Dict[str, str] = ...,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Update the status of a task.
    
    - **task_id**: The ID of the task to update
    - **status**: New status (todo, in_progress, review, done, cancelled)
    """
    try:
        new_status = status_update.get("status")
        if not new_status:
            raise ValidationError("Status is required")
        
        logger.info(f"Updating task {task_id} status to {new_status}")
        
        service = TaskService(db)
        
        # Check if task exists
        task = service.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
        # Update status
        updated_task = service.update_task_status(task_id, new_status, current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client and updated_task.crm_id:
            try:
                crm_client.tasks.update_status(updated_task.crm_id, new_status)
                logger.info(f"Task status update synced to CRM")
            except Exception as e:
                logger.warning(f"Failed to sync task status to CRM: {e}")
        
        return TaskResponse(
            data=updated_task,
            message=f"Task status updated to {new_status}"
        )
        
    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {e}")
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
        logger.error(f"Error updating task {task_id} status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task status: {str(e)}"
        )

@router.get(
    "/{task_id}/dependencies",
    response_model=List[Dict[str, Any]],
    summary="Get task dependencies",
    description="Get all dependencies for a specific task"
)
async def get_task_dependencies(
    task_id: int = Path(..., description="Task ID"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all dependencies for a specific task.
    
    - **task_id**: The ID of the task
    """
    try:
        logger.info(f"Getting dependencies for task {task_id}")
        
        service = TaskService(db)
        
        # Check if task exists
        task = service.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
        dependencies = service.get_task_dependencies(task_id)
        
        return dependencies
        
    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting dependencies for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task dependencies: {str(e)}"
        )

@router.post(
    "/{task_id}/dependencies",
    response_model=TaskResponse,
    summary="Add task dependency",
    description="Add a dependency to a task"
)
async def add_task_dependency(
    task_id: int = Path(..., description="Task ID"),
    dependency_data: Dict[str, int] = ...,
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a dependency to a task.
    
    - **task_id**: The ID of the task
    - **depends_on_id**: The ID of the task this task depends on
    """
    try:
        depends_on_id = dependency_data.get("depends_on_id")
        if not depends_on_id:
            raise ValidationError("depends_on_id is required")
        
        logger.info(f"Adding dependency from task {task_id} to task {depends_on_id}")
        
        service = TaskService(db)
        
        # Check if task exists
        task = service.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
        # Check if dependency task exists
        dependency_task = service.get_task_by_id(depends_on_id)
        if not dependency_task:
            raise TaskNotFoundError(f"Dependency task with ID {depends_on_id} not found")
        
        # Add dependency
        updated_task = service.add_task_dependency(task_id, depends_on_id)
        
        return TaskResponse(
            data=updated_task,
            message=f"Dependency added: task {task_id} depends on task {depends_on_id}"
        )
        
    except TaskNotFoundError as e:
        logger.warning(f"Task not found: {e}")
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
        logger.error(f"Error adding dependency to task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add task dependency: {str(e)}"
        )

@router.post(
    "/search",
    summary="Search tasks",
    description="Search tasks with filters similar to projects API"
)
async def search_tasks(
    request: Dict[str, Any],
    db: Session = Depends(get_database_session)
):
    """
    Search tasks with various filters.
    
    Body parameters:
    - **status**: Filter by status
    - **priority**: Filter by priority
    - **assignee**: Filter by assignee name
    - **project_id**: Filter by project ID
    - **title**: Search in task title
    - **limit**: Number of results to return (default: 50)
    - **offset**: Number of results to skip (default: 0)
    - **sort_by**: Field to sort by (default: 'id')
    - **sort_order**: Sort order (ASC/DESC, default: 'DESC')
    """
    try:
        logger.info(f"Searching tasks with filters: {request}")
        
        # Extract filters from request
        status_filter = request.get('status')
        priority = request.get('priority')
        assignee = request.get('assignee')
        project_id = request.get('project_id')
        title_search = request.get('title')
        limit = request.get('limit', 50)
        offset = request.get('offset', 0)
        sort_by = request.get('sort_by', 'id')
        sort_order = request.get('sort_order', 'DESC')
        
        # Build filters dict
        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if priority:
            filters['priority'] = priority
        if assignee:
            filters['assignee'] = assignee
        if project_id:
            filters['project_id'] = project_id
        if title_search:
            filters['search'] = title_search
        
        service = TaskService(db)
        
        # Get tasks with pagination
        page = (offset // limit) + 1
        tasks, total_count = service.get_tasks_paginated(
            page=page,
            size=limit,
            filters=filters
        )
        
        return {
            "success": True,
            "tasks": tasks,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        return {
            "success": False,
            "error": f"Failed to search tasks: {str(e)}",
            "tasks": [],
            "total": 0
        }

@router.get(
    "/stats",
    summary="Get task statistics",
    description="Get task statistics similar to projects API"
)
async def get_task_stats(
    db: Session = Depends(get_database_session)
):
    """
    Get task statistics including counts by status and priority.
    """
    try:
        logger.info("Getting task statistics")
        
        service = TaskService(db)
        
        # Get all tasks to calculate stats
        all_tasks, total_count = service.get_tasks_paginated(
            page=1,
            size=10000,  # Get all tasks
            filters={}
        )
        
        # Calculate statistics
        stats = {
            "total_tasks": total_count,
            "tasks_by_status": {},
            "tasks_by_priority": {},
            "active_tasks": 0,
            "completed_tasks": 0,
            "overdue_tasks": 0
        }
        
        # Count by status and priority
        for task in all_tasks:
            # Status counts
            status = task.get('status', 'unknown')
            stats["tasks_by_status"][status] = stats["tasks_by_status"].get(status, 0) + 1
            
            # Priority counts  
            priority = task.get('priority', 'unknown')
            stats["tasks_by_priority"][priority] = stats["tasks_by_priority"].get(priority, 0) + 1
            
            # Active tasks (not done or cancelled)
            if status not in ['done', 'cancelled']:
                stats["active_tasks"] += 1
            
            # Completed tasks
            if status == 'done':
                stats["completed_tasks"] += 1
            
            # Overdue tasks (you can implement this logic based on due_date)
            if task.get('is_overdue', False):
                stats["overdue_tasks"] += 1
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting task statistics: {e}")
        return {
            "success": False,
            "error": f"Failed to get task statistics: {str(e)}",
            "stats": {}
        }