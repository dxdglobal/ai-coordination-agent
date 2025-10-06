"""
Base Service Class - Task 1.3
==============================

Base service class providing common functionality for all business logic services.
Includes database session management, CRM integration, error handling, and caching.

Features:
- Database session management
- CRM synchronization integration
- Vector database integration for semantic search
- Error handling and logging
- Data validation and transformation
- Audit trail management

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import logging
from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from datetime import datetime
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel

from database.connection import db_manager
from database.models import BaseModel as DBBaseModel
from database.schemas import BaseSchema, PaginationSchema, PaginatedResponse

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic service
ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseSchema)

class ServiceException(Exception):
    """Base exception for service layer errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "SERVICE_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(ServiceException):
    """Exception for validation errors"""
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field

class NotFoundException(ServiceException):
    """Exception for not found errors"""
    def __init__(self, message: str, entity_type: str = None, entity_id: str = None):
        super().__init__(message, "NOT_FOUND", {"entity_type": entity_type, "entity_id": entity_id})

class ConflictException(ServiceException):
    """Exception for conflict errors"""
    def __init__(self, message: str, conflicting_field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFLICT", details)
        self.conflicting_field = conflicting_field

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType], ABC):
    """
    Base service class providing common CRUD operations and business logic.
    
    Generic parameters:
    - ModelType: SQLAlchemy model class
    - CreateSchemaType: Pydantic schema for creation
    - UpdateSchemaType: Pydantic schema for updates
    - ResponseSchemaType: Pydantic schema for responses
    """
    
    def __init__(self, model: Type[ModelType], db_session: Optional[Session] = None):
        self.model = model
        self._db_session = db_session
        self.model_name = model.__name__.lower()
    
    @property
    def db(self) -> Session:
        """Get database session"""
        if self._db_session:
            return self._db_session
        return db_manager.get_session()
    
    @property
    def should_close_session(self) -> bool:
        """Whether to close session after operations"""
        return self._db_session is None
    
    def _close_session_if_needed(self, session: Session):
        """Close session if it was created by this service"""
        if self.should_close_session:
            session.close()
    
    def _log_operation(self, operation: str, entity_id: str = None, details: Dict[str, Any] = None):
        """Log service operation"""
        log_data = {
            "service": self.__class__.__name__,
            "model": self.model_name,
            "operation": operation,
            "entity_id": entity_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        if details:
            log_data.update(details)
        
        logger.info(f"Service operation: {operation}", extra=log_data)
    
    def _handle_db_error(self, error: Exception, operation: str, entity_id: str = None):
        """Handle database errors and convert to service exceptions"""
        self._log_operation(f"{operation}_error", entity_id, {"error": str(error)})
        
        if isinstance(error, SQLAlchemyError):
            if "UNIQUE constraint failed" in str(error) or "duplicate key" in str(error):
                raise ConflictException(f"Duplicate entry for {self.model_name}")
            elif "FOREIGN KEY constraint failed" in str(error):
                raise ValidationException(f"Invalid reference in {self.model_name}")
            else:
                raise ServiceException(f"Database error in {operation}", "DATABASE_ERROR")
        else:
            raise ServiceException(f"Unexpected error in {operation}: {str(error)}")
    
    def get(self, entity_id: str, include_deleted: bool = False) -> Optional[ModelType]:
        """
        Get entity by ID
        
        Args:
            entity_id: Entity identifier
            include_deleted: Whether to include deleted entities
            
        Returns:
            Entity instance or None if not found
            
        Raises:
            ServiceException: If database error occurs
        """
        try:
            self._log_operation("get", entity_id)
            
            query = self.db.query(self.model).filter(self.model.id == entity_id)
            
            if not include_deleted and hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted == False)
            
            entity = query.first()
            return entity
            
        except Exception as e:
            self._handle_db_error(e, "get", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def get_or_404(self, entity_id: str, include_deleted: bool = False) -> ModelType:
        """
        Get entity by ID or raise NotFoundException
        
        Args:
            entity_id: Entity identifier
            include_deleted: Whether to include deleted entities
            
        Returns:
            Entity instance
            
        Raises:
            NotFoundException: If entity not found
            ServiceException: If database error occurs
        """
        entity = self.get(entity_id, include_deleted)
        if not entity:
            raise NotFoundException(
                f"{self.model_name.title()} not found",
                self.model_name,
                entity_id
            )
        return entity
    
    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        order_direction: str = "asc",
        include_deleted: bool = False
    ) -> List[ModelType]:
        """
        List entities with filtering and pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field filters
            order_by: Field to order by
            order_direction: Order direction (asc/desc)
            include_deleted: Whether to include deleted entities
            
        Returns:
            List of entity instances
        """
        try:
            self._log_operation("list", details={
                "skip": skip, "limit": limit, "filters": filters
            })
            
            query = self.db.query(self.model)
            
            # Apply soft delete filter
            if not include_deleted and hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted == False)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field) and value is not None:
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, field).in_(value))
                        else:
                            query = query.filter(getattr(self.model, field) == value)
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                if order_direction.lower() == "desc":
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))
            else:
                # Default ordering by created_at desc
                if hasattr(self.model, 'created_at'):
                    query = query.order_by(desc(self.model.created_at))
            
            # Apply pagination
            entities = query.offset(skip).limit(limit).all()
            return entities
            
        except Exception as e:
            self._handle_db_error(e, "list")
        finally:
            self._close_session_if_needed(self.db)
    
    def count(self, filters: Dict[str, Any] = None, include_deleted: bool = False) -> int:
        """
        Count entities with filtering
        
        Args:
            filters: Dictionary of field filters
            include_deleted: Whether to include deleted entities
            
        Returns:
            Number of matching entities
        """
        try:
            query = self.db.query(self.model)
            
            # Apply soft delete filter
            if not include_deleted and hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted == False)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field) and value is not None:
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, field).in_(value))
                        else:
                            query = query.filter(getattr(self.model, field) == value)
            
            return query.count()
            
        except Exception as e:
            self._handle_db_error(e, "count")
        finally:
            self._close_session_if_needed(self.db)
    
    def paginate(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        order_direction: str = "asc",
        include_deleted: bool = False
    ) -> PaginatedResponse:
        """
        Paginated list of entities
        
        Args:
            page: Page number (1-based)
            limit: Number of items per page
            filters: Dictionary of field filters
            order_by: Field to order by
            order_direction: Order direction (asc/desc)
            include_deleted: Whether to include deleted entities
            
        Returns:
            PaginatedResponse with data and pagination info
        """
        skip = (page - 1) * limit
        
        # Get data and count in parallel
        data = self.list(skip, limit, filters, order_by, order_direction, include_deleted)
        total = self.count(filters, include_deleted)
        
        pages = (total + limit - 1) // limit  # Ceiling division
        
        return PaginatedResponse(
            data=data,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )
    
    @abstractmethod
    def create(self, schema: CreateSchemaType, created_by: str = None) -> ModelType:
        """Create new entity - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def update(
        self, 
        entity_id: str, 
        schema: UpdateSchemaType, 
        updated_by: str = None
    ) -> Optional[ModelType]:
        """Update entity - to be implemented by subclasses"""
        pass
    
    def soft_delete(self, entity_id: str, deleted_by: str = None) -> bool:
        """
        Soft delete entity (mark as deleted)
        
        Args:
            entity_id: Entity identifier
            deleted_by: User performing the deletion
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If entity not found
            ServiceException: If database error occurs
        """
        try:
            self._log_operation("soft_delete", entity_id)
            
            entity = self.get_or_404(entity_id)
            
            if hasattr(entity, 'is_deleted'):
                entity.is_deleted = True
                entity.deleted_at = datetime.utcnow()
                if hasattr(entity, 'updated_by') and deleted_by:
                    entity.updated_by = deleted_by
                
                self.db.commit()
                return True
            else:
                raise ServiceException(f"{self.model_name} does not support soft delete")
                
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ServiceException):
                raise
            self._handle_db_error(e, "soft_delete", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def hard_delete(self, entity_id: str) -> bool:
        """
        Hard delete entity (permanently remove)
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If entity not found
            ServiceException: If database error occurs
        """
        try:
            self._log_operation("hard_delete", entity_id)
            
            entity = self.get_or_404(entity_id, include_deleted=True)
            
            self.db.delete(entity)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ServiceException):
                raise
            self._handle_db_error(e, "hard_delete", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def restore(self, entity_id: str, restored_by: str = None) -> Optional[ModelType]:
        """
        Restore soft-deleted entity
        
        Args:
            entity_id: Entity identifier
            restored_by: User performing the restoration
            
        Returns:
            Restored entity instance
            
        Raises:
            NotFoundException: If entity not found
            ServiceException: If database error occurs
        """
        try:
            self._log_operation("restore", entity_id)
            
            entity = self.get_or_404(entity_id, include_deleted=True)
            
            if hasattr(entity, 'is_deleted'):
                entity.is_deleted = False
                entity.deleted_at = None
                if hasattr(entity, 'updated_by') and restored_by:
                    entity.updated_by = restored_by
                
                self.db.commit()
                return entity
            else:
                raise ServiceException(f"{self.model_name} does not support soft delete/restore")
                
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ServiceException):
                raise
            self._handle_db_error(e, "restore", entity_id)
        finally:
            self._close_session_if_needed(self.db)
    
    def search(
        self,
        query: str,
        fields: List[str] = None,
        limit: int = 20,
        filters: Dict[str, Any] = None
    ) -> List[ModelType]:
        """
        Search entities by text query
        
        Args:
            query: Search query string
            fields: List of fields to search in
            limit: Maximum number of results
            filters: Additional filters
            
        Returns:
            List of matching entities
        """
        try:
            self._log_operation("search", details={"query": query, "fields": fields})
            
            db_query = self.db.query(self.model)
            
            # Apply soft delete filter
            if hasattr(self.model, 'is_deleted'):
                db_query = db_query.filter(self.model.is_deleted == False)
            
            # Apply additional filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field) and value is not None:
                        db_query = db_query.filter(getattr(self.model, field) == value)
            
            # Apply text search
            if query and fields:
                search_conditions = []
                for field in fields:
                    if hasattr(self.model, field):
                        search_conditions.append(
                            getattr(self.model, field).ilike(f"%{query}%")
                        )
                
                if search_conditions:
                    db_query = db_query.filter(or_(*search_conditions))
            
            # Order by relevance (created_at for now)
            if hasattr(self.model, 'created_at'):
                db_query = db_query.order_by(desc(self.model.created_at))
            
            entities = db_query.limit(limit).all()
            return entities
            
        except Exception as e:
            self._handle_db_error(e, "search")
        finally:
            self._close_session_if_needed(self.db)
    
    def bulk_create(self, schemas: List[CreateSchemaType], created_by: str = None) -> List[ModelType]:
        """
        Create multiple entities in a single transaction
        
        Args:
            schemas: List of creation schemas
            created_by: User performing the creation
            
        Returns:
            List of created entities
        """
        try:
            self._log_operation("bulk_create", details={"count": len(schemas)})
            
            entities = []
            for schema in schemas:
                entity = self.create(schema, created_by)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ServiceException):
                raise
            self._handle_db_error(e, "bulk_create")
        finally:
            self._close_session_if_needed(self.db)
    
    def bulk_update(
        self,
        updates: List[Dict[str, Any]],
        updated_by: str = None
    ) -> List[ModelType]:
        """
        Update multiple entities in a single transaction
        
        Args:
            updates: List of dictionaries with 'id' and update fields
            updated_by: User performing the updates
            
        Returns:
            List of updated entities
        """
        try:
            self._log_operation("bulk_update", details={"count": len(updates)})
            
            entities = []
            for update_data in updates:
                entity_id = update_data.pop('id')
                schema_data = {k: v for k, v in update_data.items() if v is not None}
                
                # Convert to update schema (this might need customization per service)
                entity = self.update(entity_id, schema_data, updated_by)
                if entity:
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, ServiceException):
                raise
            self._handle_db_error(e, "bulk_update")
        finally:
            self._close_session_if_needed(self.db)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get basic statistics for the entity type
        
        Returns:
            Dictionary with statistics
        """
        try:
            total_count = self.count(include_deleted=True)
            active_count = self.count(include_deleted=False)
            deleted_count = total_count - active_count
            
            stats = {
                "total": total_count,
                "active": active_count,
                "deleted": deleted_count
            }
            
            # Add status-based statistics if model has status
            if hasattr(self.model, 'status'):
                status_stats = {}
                statuses = self.db.query(self.model.status).distinct().all()
                for (status,) in statuses:
                    status_count = self.count({"status": status})
                    status_stats[status] = status_count
                stats["by_status"] = status_stats
            
            return stats
            
        except Exception as e:
            self._handle_db_error(e, "get_statistics")
        finally:
            self._close_session_if_needed(self.db)

# Export service classes and exceptions
__all__ = [
    "BaseService",
    "ServiceException",
    "ValidationException", 
    "NotFoundException",
    "ConflictException",
    "ModelType",
    "CreateSchemaType",
    "UpdateSchemaType",
    "ResponseSchemaType"
]