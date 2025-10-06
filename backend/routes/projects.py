"""
Projects API Routes - Task 1.3
==============================

FastAPI routes for project management including:
- CRUD operations for projects
- Project-task relationships
- Project team management
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
from database.models import Project as DBProject, Task as DBTask, User as DBUser
from schemas.project_schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, 
    ProjectListResponse, ProjectWithTasks
)
from services.project_service import ProjectService
from core.dependencies import get_current_user, get_crm_client
from core.pagination import PaginationParams, paginate
from core.exceptions import ProjectNotFoundError, ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="Get all projects",
    description="Retrieve a paginated list of projects with optional filtering"
)
async def get_projects(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None, description="Filter by project status"),
    priority: Optional[str] = Query(None, description="Filter by priority level"), 
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    manager_id: Optional[int] = Query(None, description="Filter by manager ID"),
    search: Optional[str] = Query(None, description="Search in project name/description"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all projects with optional filtering and pagination.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 50, max: 100)
    - **status**: Filter by project status (active, completed, on_hold, cancelled)
    - **priority**: Filter by priority (low, medium, high, critical)
    - **client_id**: Filter by client ID
    - **manager_id**: Filter by manager ID  
    - **search**: Search term for name/description
    """
    try:
        logger.info(f"Getting projects for user {current_user.get('id')} with filters: status={status_filter}, priority={priority}")
        
        service = ProjectService(db)
        
        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if priority:
            filters['priority'] = priority
        if client_id:
            filters['client_id'] = client_id
        if manager_id:
            filters['manager_id'] = manager_id
        if search:
            filters['search'] = search
        
        projects, total_count = service.get_projects_paginated(
            page=pagination.page,
            size=pagination.size,
            filters=filters
        )
        
        return ProjectListResponse(
            data=projects,
            total=total_count,
            page=pagination.page,
            size=pagination.size,
            pages=(total_count + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieve a specific project by its ID"
)
async def get_project(
    project_id: int = Path(..., description="Project ID"),
    include_tasks: bool = Query(False, description="Include project tasks"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific project by ID.
    
    - **project_id**: The ID of the project to retrieve
    - **include_tasks**: Whether to include project tasks in response
    """
    try:
        logger.info(f"Getting project {project_id} for user {current_user.get('id')}")
        
        service = ProjectService(db)
        project = service.get_project_by_id(project_id, include_tasks=include_tasks)
        
        if not project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        
        return ProjectResponse(data=project)
        
    except ProjectNotFoundError as e:
        logger.warning(f"Project not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project: {str(e)}"
        )

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new project",
    description="Create a new project"
)
async def create_project(
    project_data: ProjectCreate,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Create a new project.
    
    - **name**: Project name (required)
    - **description**: Project description
    - **status**: Project status (default: active)
    - **priority**: Priority level (default: medium)
    - **start_date**: Project start date
    - **end_date**: Project end date
    - **budget**: Project budget
    - **client_id**: Associated client ID
    - **manager_id**: Project manager ID
    - **team_members**: List of team member IDs
    """
    try:
        logger.info(f"Creating project '{project_data.name}' for user {current_user.get('id')}")
        
        service = ProjectService(db)
        
        # Set creator as manager if not specified
        if not project_data.manager_id:
            project_data.manager_id = current_user.get('id')
        
        # Create project in database
        project = service.create_project(project_data, creator_id=current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client:
            try:
                from crm_api_endpoints import Project as CRMProject
                crm_project = CRMProject(
                    name=project.name,
                    description=project.description,
                    status=project.status,
                    priority=project.priority,
                    start_date=project.start_date.isoformat() if project.start_date else None,
                    end_date=project.end_date.isoformat() if project.end_date else None,
                    budget=float(project.budget) if project.budget else None,
                    client_id=project.client_id,
                    manager_id=project.manager_id
                )
                
                crm_response = crm_client.projects.create(crm_project)
                service.update_crm_id(project.id, crm_response.id)
                logger.info(f"Project {project.id} synced to CRM with ID {crm_response.id}")
                
            except Exception as e:
                logger.warning(f"Failed to sync project to CRM: {e}")
        
        return ProjectResponse(
            data=project,
            message="Project created successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update an existing project"
)
async def update_project(
    project_id: int = Path(..., description="Project ID"),
    project_data: ProjectUpdate = ...,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Update an existing project.
    
    - **project_id**: The ID of the project to update
    - Only provided fields will be updated
    """
    try:
        logger.info(f"Updating project {project_id} for user {current_user.get('id')}")
        
        service = ProjectService(db)
        
        # Check if project exists
        existing_project = service.get_project_by_id(project_id)
        if not existing_project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        
        # Update project
        project = service.update_project(project_id, project_data, updater_id=current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client and project.crm_id:
            try:
                from crm_api_endpoints import Project as CRMProject
                crm_project = CRMProject(
                    id=project.crm_id,
                    name=project.name,
                    description=project.description,
                    status=project.status,
                    priority=project.priority,
                    start_date=project.start_date.isoformat() if project.start_date else None,
                    end_date=project.end_date.isoformat() if project.end_date else None,
                    budget=float(project.budget) if project.budget else None,
                    client_id=project.client_id,
                    manager_id=project.manager_id
                )
                
                crm_client.projects.update(project.crm_id, crm_project)
                logger.info(f"Project {project.id} synced to CRM")
                
            except Exception as e:
                logger.warning(f"Failed to sync project update to CRM: {e}")
        
        return ProjectResponse(
            data=project,
            message="Project updated successfully"
        )
        
    except ProjectNotFoundError as e:
        logger.warning(f"Project not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Validation error updating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project"
)
async def delete_project(
    project_id: int = Path(..., description="Project ID"),
    sync_to_crm: bool = Query(True, description="Sync deletion to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Delete a project.
    
    - **project_id**: The ID of the project to delete
    - This will also delete all associated tasks
    """
    try:
        logger.info(f"Deleting project {project_id} for user {current_user.get('id')}")
        
        service = ProjectService(db)
        
        # Check if project exists
        project = service.get_project_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        
        # Delete from CRM first if needed
        if sync_to_crm and crm_client and project.crm_id:
            try:
                crm_client.projects.delete(project.crm_id)
                logger.info(f"Project {project_id} deleted from CRM")
            except Exception as e:
                logger.warning(f"Failed to delete project from CRM: {e}")
        
        # Delete from database
        service.delete_project(project_id, deleter_id=current_user.get('id'))
        
        logger.info(f"Project {project_id} deleted successfully")
        
    except ProjectNotFoundError as e:
        logger.warning(f"Project not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

@router.get(
    "/{project_id}/tasks",
    response_model=List[Dict[str, Any]],
    summary="Get project tasks",
    description="Get all tasks for a specific project"
)
async def get_project_tasks(
    project_id: int = Path(..., description="Project ID"),
    status_filter: Optional[str] = Query(None, description="Filter by task status"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all tasks for a specific project.
    
    - **project_id**: The ID of the project
    - **status**: Filter by task status
    - **assignee_id**: Filter by assignee ID
    """
    try:
        logger.info(f"Getting tasks for project {project_id}")
        
        service = ProjectService(db)
        
        # Check if project exists
        project = service.get_project_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        
        filters = {"project_id": project_id}
        if status_filter:
            filters["status"] = status_filter
        if assignee_id:
            filters["assignee_id"] = assignee_id
        
        tasks = service.get_project_tasks(project_id, filters)
        
        return tasks
        
    except ProjectNotFoundError as e:
        logger.warning(f"Project not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting tasks for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project tasks: {str(e)}"
        )

@router.post(
    "/{project_id}/team",
    response_model=ProjectResponse,
    summary="Add team member",
    description="Add a team member to the project"
)
async def add_team_member(
    project_id: int = Path(..., description="Project ID"),
    user_id: int = Query(..., description="User ID to add to team"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a team member to the project.
    
    - **project_id**: The ID of the project
    - **user_id**: The ID of the user to add to the team
    """
    try:
        logger.info(f"Adding user {user_id} to project {project_id} team")
        
        service = ProjectService(db)
        
        # Check if project exists
        project = service.get_project_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        
        # Add team member
        updated_project = service.add_team_member(project_id, user_id)
        
        return ProjectResponse(
            data=updated_project,
            message=f"User {user_id} added to project team"
        )
        
    except ProjectNotFoundError as e:
        logger.warning(f"Project not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding team member to project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add team member: {str(e)}"
        )

@router.delete(
    "/{project_id}/team/{user_id}",
    response_model=ProjectResponse,
    summary="Remove team member",
    description="Remove a team member from the project"
)
async def remove_team_member(
    project_id: int = Path(..., description="Project ID"),
    user_id: int = Path(..., description="User ID to remove from team"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a team member from the project.
    
    - **project_id**: The ID of the project
    - **user_id**: The ID of the user to remove from the team
    """
    try:
        logger.info(f"Removing user {user_id} from project {project_id} team")
        
        service = ProjectService(db)
        
        # Check if project exists
        project = service.get_project_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        
        # Remove team member
        updated_project = service.remove_team_member(project_id, user_id)
        
        return ProjectResponse(
            data=updated_project,
            message=f"User {user_id} removed from project team"
        )
        
    except ProjectNotFoundError as e:
        logger.warning(f"Project not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing team member from project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove team member: {str(e)}"
        )