"""
Clients API Routes - Task 1.3
=============================

FastAPI routes for client management including:
- CRUD operations for clients
- Client-project relationships
- Client contact management
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
from database.models import Client as DBClient, Project as DBProject, User as DBUser
from schemas.client_schemas import (
    ClientCreate, ClientUpdate, ClientResponse, 
    ClientListResponse, ClientWithProjects
)
from services.client_service import ClientService
from core.dependencies import get_current_user, get_crm_client
from core.pagination import PaginationParams, paginate
from core.exceptions import ClientNotFoundError, ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/",
    response_model=ClientListResponse,
    summary="Get all clients",
    description="Retrieve a paginated list of clients with optional filtering"
)
async def get_clients(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None, description="Filter by client status"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    search: Optional[str] = Query(None, description="Search in client name/company"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all clients with optional filtering and pagination.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 50, max: 100)
    - **status**: Filter by client status (active, inactive, prospect, former)
    - **industry**: Filter by industry
    - **search**: Search term for name/company
    """
    try:
        logger.info(f"Getting clients for user {current_user.get('id')} with filters")
        
        service = ClientService(db)
        
        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if industry:
            filters['industry'] = industry
        if search:
            filters['search'] = search
        
        clients, total_count = service.get_clients_paginated(
            page=pagination.page,
            size=pagination.size,
            filters=filters
        )
        
        return ClientListResponse(
            data=clients,
            total=total_count,
            page=pagination.page,
            size=pagination.size,
            pages=(total_count + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"Error getting clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve clients: {str(e)}"
        )

@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Get client by ID",
    description="Retrieve a specific client by their ID"
)
async def get_client(
    client_id: int = Path(..., description="Client ID"),
    include_projects: bool = Query(False, description="Include client's projects"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific client by ID.
    
    - **client_id**: The ID of the client to retrieve
    - **include_projects**: Whether to include client's projects in response
    """
    try:
        logger.info(f"Getting client {client_id} for user {current_user.get('id')}")
        
        service = ClientService(db)
        client = service.get_client_by_id(client_id, include_projects=include_projects)
        
        if not client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        return ClientResponse(data=client)
        
    except ClientNotFoundError as e:
        logger.warning(f"Client not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client: {str(e)}"
        )

@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new client",
    description="Create a new client"
)
async def create_client(
    client_data: ClientCreate,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Create a new client.
    
    - **name**: Client name (required)
    - **company**: Company name
    - **email**: Email address
    - **phone**: Phone number
    - **address**: Physical address
    - **industry**: Industry type
    - **status**: Client status (default: active)
    - **contact_person**: Primary contact person
    - **notes**: Additional notes
    """
    try:
        logger.info(f"Creating client '{client_data.name}' for user {current_user.get('id')}")
        
        service = ClientService(db)
        
        # Create client in database
        client = service.create_client(client_data, creator_id=current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client:
            try:
                from crm_api_endpoints import Client as CRMClient
                crm_client_obj = CRMClient(
                    name=client.name,
                    company=client.company,
                    email=client.email,
                    phone=client.phone,
                    address=client.address,
                    industry=client.industry,
                    status=client.status,
                    contact_person=client.contact_person,
                    notes=client.notes
                )
                
                crm_response = crm_client.clients.create(crm_client_obj)
                service.update_crm_id(client.id, crm_response.id)
                logger.info(f"Client {client.id} synced to CRM with ID {crm_response.id}")
                
            except Exception as e:
                logger.warning(f"Failed to sync client to CRM: {e}")
        
        return ClientResponse(
            data=client,
            message="Client created successfully"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error creating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}"
        )

@router.put(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update client",
    description="Update an existing client"
)
async def update_client(
    client_id: int = Path(..., description="Client ID"),
    client_data: ClientUpdate = ...,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Update an existing client.
    
    - **client_id**: The ID of the client to update
    - Only provided fields will be updated
    """
    try:
        logger.info(f"Updating client {client_id} for user {current_user.get('id')}")
        
        service = ClientService(db)
        
        # Check if client exists
        existing_client = service.get_client_by_id(client_id)
        if not existing_client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        # Update client
        client = service.update_client(client_id, client_data, updater_id=current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client and client.crm_id:
            try:
                from crm_api_endpoints import Client as CRMClient
                crm_client_obj = CRMClient(
                    id=client.crm_id,
                    name=client.name,
                    company=client.company,
                    email=client.email,
                    phone=client.phone,
                    address=client.address,
                    industry=client.industry,
                    status=client.status,
                    contact_person=client.contact_person,
                    notes=client.notes
                )
                
                crm_client.clients.update(client.crm_id, crm_client_obj)
                logger.info(f"Client {client.id} synced to CRM")
                
            except Exception as e:
                logger.warning(f"Failed to sync client update to CRM: {e}")
        
        return ClientResponse(
            data=client,
            message="Client updated successfully"
        )
        
    except ClientNotFoundError as e:
        logger.warning(f"Client not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Validation error updating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client: {str(e)}"
        )

@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete client",
    description="Delete a client"
)
async def delete_client(
    client_id: int = Path(..., description="Client ID"),
    sync_to_crm: bool = Query(True, description="Sync deletion to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Delete a client.
    
    - **client_id**: The ID of the client to delete
    - This will also update all associated projects
    """
    try:
        logger.info(f"Deleting client {client_id} for user {current_user.get('id')}")
        
        service = ClientService(db)
        
        # Check if client exists
        client = service.get_client_by_id(client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        # Delete from CRM first if needed
        if sync_to_crm and crm_client and client.crm_id:
            try:
                crm_client.clients.delete(client.crm_id)
                logger.info(f"Client {client_id} deleted from CRM")
            except Exception as e:
                logger.warning(f"Failed to delete client from CRM: {e}")
        
        # Delete from database
        service.delete_client(client_id, deleter_id=current_user.get('id'))
        
        logger.info(f"Client {client_id} deleted successfully")
        
    except ClientNotFoundError as e:
        logger.warning(f"Client not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete client: {str(e)}"
        )

@router.get(
    "/{client_id}/projects",
    response_model=List[Dict[str, Any]],
    summary="Get client projects",
    description="Get all projects for a specific client"
)
async def get_client_projects(
    client_id: int = Path(..., description="Client ID"),
    status_filter: Optional[str] = Query(None, description="Filter by project status"),
    manager_id: Optional[int] = Query(None, description="Filter by project manager"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all projects for a specific client.
    
    - **client_id**: The ID of the client
    - **status**: Filter by project status
    - **manager_id**: Filter by project manager ID
    """
    try:
        logger.info(f"Getting projects for client {client_id}")
        
        service = ClientService(db)
        
        # Check if client exists
        client = service.get_client_by_id(client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        filters = {"client_id": client_id}
        if status_filter:
            filters["status"] = status_filter
        if manager_id:
            filters["manager_id"] = manager_id
        
        projects = service.get_client_projects(client_id, filters)
        
        return projects
        
    except ClientNotFoundError as e:
        logger.warning(f"Client not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting projects for client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client projects: {str(e)}"
        )

@router.patch(
    "/{client_id}/status",
    response_model=ClientResponse,
    summary="Update client status",
    description="Update the status of a client"
)
async def update_client_status(
    client_id: int = Path(..., description="Client ID"),
    status_update: Dict[str, str] = ...,
    sync_to_crm: bool = Query(True, description="Sync to CRM system"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user),
    crm_client = Depends(get_crm_client)
):
    """
    Update the status of a client.
    
    - **client_id**: The ID of the client to update
    - **status**: New status (active, inactive, prospect, former)
    """
    try:
        new_status = status_update.get("status")
        if not new_status:
            raise ValidationError("Status is required")
        
        logger.info(f"Updating client {client_id} status to {new_status}")
        
        service = ClientService(db)
        
        # Check if client exists
        client = service.get_client_by_id(client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        # Update status
        updated_client = service.update_client_status(client_id, new_status, current_user.get('id'))
        
        # Sync to CRM if requested and available
        if sync_to_crm and crm_client and updated_client.crm_id:
            try:
                from crm_api_endpoints import Client as CRMClient
                crm_client_obj = CRMClient(
                    id=updated_client.crm_id,
                    name=updated_client.name,
                    company=updated_client.company,
                    email=updated_client.email,
                    phone=updated_client.phone,
                    address=updated_client.address,
                    industry=updated_client.industry,
                    status=updated_client.status,
                    contact_person=updated_client.contact_person,
                    notes=updated_client.notes
                )
                crm_client.clients.update(updated_client.crm_id, crm_client_obj)
                logger.info(f"Client status update synced to CRM")
            except Exception as e:
                logger.warning(f"Failed to sync client status to CRM: {e}")
        
        return ClientResponse(
            data=updated_client,
            message=f"Client status updated to {new_status}"
        )
        
    except ClientNotFoundError as e:
        logger.warning(f"Client not found: {e}")
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
        logger.error(f"Error updating client {client_id} status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client status: {str(e)}"
        )

@router.get(
    "/search",
    response_model=ClientListResponse,
    summary="Search clients",
    description="Search clients using vector search capabilities"
)
async def search_clients(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results"),
    include_similar: bool = Query(True, description="Include semantically similar results"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Search clients using vector search capabilities.
    
    - **query**: Search query (can include natural language)
    - **limit**: Maximum number of results to return
    - **include_similar**: Whether to include semantically similar results
    """
    try:
        logger.info(f"Searching clients with query: {query}")
        
        service = ClientService(db)
        
        # Perform vector search
        clients, total_count = service.search_clients_vector(
            query=query,
            limit=limit,
            include_similar=include_similar
        )
        
        return ClientListResponse(
            data=clients,
            total=total_count,
            page=1,
            size=limit,
            pages=1,
            search_query=query
        )
        
    except Exception as e:
        logger.error(f"Error searching clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search clients: {str(e)}"
        )

@router.get(
    "/{client_id}/stats",
    response_model=Dict[str, Any],
    summary="Get client statistics",
    description="Get comprehensive statistics for a client"
)
async def get_client_stats(
    client_id: int = Path(..., description="Client ID"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive statistics for a client.
    
    - **client_id**: The ID of the client
    """
    try:
        logger.info(f"Getting statistics for client {client_id}")
        
        service = ClientService(db)
        
        # Check if client exists
        client = service.get_client_by_id(client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        # Get client statistics
        stats = service.get_client_statistics(client_id)
        
        return stats
        
    except ClientNotFoundError as e:
        logger.warning(f"Client not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting statistics for client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client statistics: {str(e)}"
        )