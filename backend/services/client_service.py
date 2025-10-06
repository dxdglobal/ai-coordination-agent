"""
Client Service - Task 1.3
==========================

Business logic service for client management with CRM integration and project relationships.
Handles client lifecycle, project associations, and relationship management.

Features:
- Client CRUD operations with validation
- Project relationship management
- CRM synchronization
- Vector database integration for semantic search
- Client statistics and analytics
- Search and filtering capabilities

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
from database.models import Client, ClientStatus, Project, ProjectStatus
from database.schemas import (
    ClientCreate, ClientUpdate, ClientResponse, ClientStatistics
)

# Configure logging
logger = logging.getLogger(__name__)

class ClientService(BaseService[Client, ClientCreate, ClientUpdate, ClientResponse]):
    """Service for client management and relationship tracking"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(Client, db_session)
    
    def _validate_email_format(self, email: str) -> None:
        """
        Validate email format
        
        Args:
            email: Email to validate
            
        Raises:
            ValidationException: If email format is invalid
        """
        if email and "@" not in email:
            raise ValidationException("Invalid email format", "email")
    
    def _validate_website_format(self, website: str) -> None:
        """
        Validate website URL format
        
        Args:
            website: Website URL to validate
            
        Raises:
            ValidationException: If website format is invalid
        """
        if website and not (website.startswith("http://") or website.startswith("https://")):
            raise ValidationException("Website must start with http:// or https://", "website")
    
    def create(self, schema: ClientCreate, created_by: str = None) -> Client:
        """
        Create new client with validation
        
        Args:
            schema: Client creation data
            created_by: User performing the creation
            
        Returns:
            Created client instance
            
        Raises:
            ConflictException: If email already exists
            ValidationException: If data validation fails
        """
        try:
            self._log_operation("create_client", details={"name": schema.name})
            
            # Validate email format
            if schema.email:
                self._validate_email_format(schema.email)
                
                # Check for existing email
                existing_client = self.db.query(Client).filter(
                    Client.email == schema.email,
                    Client.is_deleted == False
                ).first()
                
                if existing_client:
                    raise ConflictException("Email already exists", "email")
            
            # Validate website format
            if schema.website:
                self._validate_website_format(schema.website)
            
            # Create client
            client_data = schema.dict()
            client = Client(
                **client_data,
                created_by=created_by,
                acquisition_date=date.today()
            )
            
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
            
            self._log_operation("client_created", client.id)
            
            # TODO: Trigger CRM sync
            # self._sync_to_crm(client, "create")
            
            # TODO: Add to vector database for semantic search
            # self._add_to_vector_db(client)
            
            return client
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (ConflictException, ValidationException)):
                raise
            self._handle_db_error(e, "create_client")
        finally:
            self._close_session_if_needed(self.db)
    
    def update(self, entity_id: str, schema: ClientUpdate, updated_by: str = None) -> Optional[Client]:
        """
        Update client information
        
        Args:
            entity_id: Client ID
            schema: Update data
            updated_by: User performing the update
            
        Returns:
            Updated client instance
            
        Raises:
            NotFoundException: If client not found
            ConflictException: If email conflicts
        """
        try:
            self._log_operation("update_client", entity_id)
            
            client = self.get_or_404(entity_id)
            
            # Validate email if provided
            if schema.email:
                self._validate_email_format(schema.email)
                
                # Check for email conflicts
                if schema.email != client.email:
                    existing_client = self.db.query(Client).filter(
                        Client.email == schema.email,
                        Client.id != entity_id,
                        Client.is_deleted == False
                    ).first()
                    
                    if existing_client:
                        raise ConflictException("Email already exists", "email")
            
            # Validate website if provided
            if schema.website:
                self._validate_website_format(schema.website)
            
            # Update fields
            update_data = schema.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(client, field):
                    setattr(client, field, value)
            
            client.updated_by = updated_by
            client.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(client)
            
            self._log_operation("client_updated", entity_id)
            
            # TODO: Trigger CRM sync
            # self._sync_to_crm(client, "update")
            
            # TODO: Update vector database
            # self._update_vector_db(client)
            
            return client
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (NotFoundException, ConflictException, ValidationException)):
                raise
            self._handle_db_error(e, "update_client", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_with_projects(self, entity_id: str) -> Optional[Client]:
        """
        Get client with related projects
        
        Args:
            entity_id: Client ID
            
        Returns:
            Client with projects loaded
        """
        try:
            client = self.db.query(Client).options(
                joinedload(Client.projects)
            ).filter(
                Client.id == entity_id,
                Client.is_deleted == False
            ).first()
            
            return client
            
        except Exception as e:
            self._handle_db_error(e, "get_with_projects", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_email(self, email: str) -> Optional[Client]:
        """
        Get client by email
        
        Args:
            email: Email to search for
            
        Returns:
            Client instance or None
        """
        try:
            client = self.db.query(Client).filter(
                Client.email == email,
                Client.is_deleted == False
            ).first()
            
            return client
            
        except Exception as e:
            self._handle_db_error(e, "get_by_email")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_company(self, company: str) -> List[Client]:
        """
        Get clients by company name
        
        Args:
            company: Company name to search for
            
        Returns:
            List of clients from the company
        """
        try:
            clients = self.db.query(Client).filter(
                Client.company.ilike(f"%{company}%"),
                Client.is_deleted == False
            ).order_by(Client.name).all()
            
            return clients
            
        except Exception as e:
            self._handle_db_error(e, "get_by_company")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_by_industry(self, industry: str, status: ClientStatus = None) -> List[Client]:
        """
        Get clients by industry
        
        Args:
            industry: Industry to filter by
            status: Optional status filter
            
        Returns:
            List of clients in the industry
        """
        try:
            query = self.db.query(Client).filter(
                Client.industry == industry,
                Client.is_deleted == False
            )
            
            if status:
                query = query.filter(Client.status == status)
            
            clients = query.order_by(Client.name).all()
            return clients
            
        except Exception as e:
            self._handle_db_error(e, "get_by_industry")
        finally:
            self._close_session_if_needed(self.db)
    
    def search_clients(
        self,
        query: str,
        industry: str = None,
        status: ClientStatus = None,
        limit: int = 20
    ) -> List[Client]:
        """
        Search clients by name, company, or email
        
        Args:
            query: Search query
            industry: Optional industry filter
            status: Optional status filter
            limit: Maximum number of results
            
        Returns:
            List of matching clients
        """
        try:
            db_query = self.db.query(Client).filter(Client.is_deleted == False)
            
            # Apply text search
            if query:
                search_conditions = [
                    Client.name.ilike(f"%{query}%"),
                    Client.company.ilike(f"%{query}%"),
                    Client.email.ilike(f"%{query}%")
                ]
                db_query = db_query.filter(or_(*search_conditions))
            
            # Apply filters
            if industry:
                db_query = db_query.filter(Client.industry == industry)
            if status:
                db_query = db_query.filter(Client.status == status)
            
            clients = db_query.order_by(Client.name).limit(limit).all()
            return clients
            
        except Exception as e:
            self._handle_db_error(e, "search_clients")
        finally:
            self._close_session_if_needed(self.db)
    
    def update_client_status(self, client_id: str, status: ClientStatus, updated_by: str = None) -> Optional[Client]:
        """
        Update client status
        
        Args:
            client_id: Client ID
            status: New status
            updated_by: User performing the update
            
        Returns:
            Updated client
        """
        try:
            self._log_operation("update_client_status", client_id, {"status": status})
            
            client = self.get_or_404(client_id)
            
            client.status = status
            client.updated_by = updated_by
            client.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(client)
            
            self._log_operation("client_status_updated", client_id)
            
            return client
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, NotFoundException):
                raise
            self._handle_db_error(e, "update_client_status", client_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_client_projects(self, client_id: str, status: ProjectStatus = None) -> List[Project]:
        """
        Get projects for a specific client
        
        Args:
            client_id: Client ID
            status: Optional project status filter
            
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
            self._handle_db_error(e, "get_client_projects")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_client_revenue(self, client_id: str) -> Dict[str, Any]:
        """
        Calculate client revenue from projects
        
        Args:
            client_id: Client ID
            
        Returns:
            Dictionary with revenue information
        """
        try:
            projects = self.get_client_projects(client_id)
            
            total_budget = sum([p.budget or 0 for p in projects])
            active_budget = sum([p.budget or 0 for p in projects if p.status in [ProjectStatus.PLANNING, ProjectStatus.ACTIVE]])
            completed_budget = sum([p.budget or 0 for p in projects if p.status == ProjectStatus.COMPLETED])
            
            return {
                "total_projects": len(projects),
                "total_budget": total_budget,
                "active_budget": active_budget,
                "completed_budget": completed_budget,
                "active_projects": len([p for p in projects if p.status in [ProjectStatus.PLANNING, ProjectStatus.ACTIVE]]),
                "completed_projects": len([p for p in projects if p.status == ProjectStatus.COMPLETED])
            }
            
        except Exception as e:
            self._handle_db_error(e, "get_client_revenue")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_top_clients_by_revenue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top clients by total project budget
        
        Args:
            limit: Number of top clients to return
            
        Returns:
            List of clients with revenue information
        """
        try:
            # Query to get client revenue
            result = self.db.query(
                Client.id,
                Client.name,
                Client.company,
                func.sum(Project.budget).label('total_budget'),
                func.count(Project.id).label('project_count')
            ).join(
                Project, Client.id == Project.client_id
            ).filter(
                Client.is_deleted == False,
                Project.is_deleted == False
            ).group_by(
                Client.id, Client.name, Client.company
            ).order_by(
                func.sum(Project.budget).desc()
            ).limit(limit).all()
            
            top_clients = []
            for row in result:
                top_clients.append({
                    "client_id": row.id,
                    "name": row.name,
                    "company": row.company,
                    "total_budget": float(row.total_budget or 0),
                    "project_count": row.project_count
                })
            
            return top_clients
            
        except Exception as e:
            self._handle_db_error(e, "get_top_clients_by_revenue")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_clients_by_status(self, status: ClientStatus) -> List[Client]:
        """
        Get clients by status
        
        Args:
            status: Client status to filter by
            
        Returns:
            List of clients with the specified status
        """
        try:
            clients = self.db.query(Client).filter(
                Client.status == status,
                Client.is_deleted == False
            ).order_by(Client.name).all()
            
            return clients
            
        except Exception as e:
            self._handle_db_error(e, "get_clients_by_status")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_client_statistics(self) -> ClientStatistics:
        """
        Get client statistics
        
        Returns:
            Client statistics
        """
        try:
            total_clients = self.count()
            active_clients = self.count({"status": ClientStatus.ACTIVE})
            
            # Get project and revenue statistics
            project_result = self.db.query(
                func.count(Project.id).label('total_projects'),
                func.sum(Project.budget).label('total_revenue')
            ).join(
                Client, Project.client_id == Client.id
            ).filter(
                Client.is_deleted == False,
                Project.is_deleted == False
            ).first()
            
            total_projects = project_result.total_projects or 0
            total_revenue = project_result.total_revenue
            
            return ClientStatistics(
                total_clients=total_clients,
                active_clients=active_clients,
                total_projects=total_projects,
                total_revenue=total_revenue
            )
            
        except Exception as e:
            self._handle_db_error(e, "get_client_statistics")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_recent_clients(self, days: int = 30, limit: int = 10) -> List[Client]:
        """
        Get recently added clients
        
        Args:
            days: Number of days to look back
            limit: Maximum number of clients to return
            
        Returns:
            List of recently added clients
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            clients = self.db.query(Client).filter(
                Client.created_at >= cutoff_date,
                Client.is_deleted == False
            ).order_by(Client.created_at.desc()).limit(limit).all()
            
            return clients
            
        except Exception as e:
            self._handle_db_error(e, "get_recent_clients")
        finally:
            self._close_session_if_needed(self.db)
    
    def vector_search_clients(self, query: str, limit: int = 10) -> List[Client]:
        """
        Search clients using vector similarity (placeholder for future implementation)
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of similar clients
        """
        try:
            # For now, fall back to text search
            # TODO: Implement actual vector search integration
            return self.search_clients(query, limit=limit)
            
        except Exception as e:
            self._handle_db_error(e, "vector_search_clients")
        finally:
            self._close_session_if_needed(self.db)

# Export service
__all__ = ["ClientService"]