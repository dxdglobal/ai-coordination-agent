"""
Exception Handlers - Task 1.3
==============================

Comprehensive exception handling for FastAPI application.
Custom exceptions, error responses, and global exception handlers.

Features:
- Custom exception classes with error codes
- HTTP exception mapping
- Validation error handling
- Database error handling
- Structured error responses
- Error logging and monitoring

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import traceback

from core.logging_config import get_logger
from database.schemas import ErrorResponse, ValidationErrorResponse, ErrorDetail

# Configure logging
logger = get_logger(__name__)

class AppException(Exception):
    """Base application exception"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(AppException):
    """Validation error exception"""
    
    def __init__(
        self,
        message: str,
        field: str = None,
        details: Dict[str, Any] = None
    ):
        super().__init__(
            message,
            "VALIDATION_ERROR",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            details
        )
        self.field = field

class NotFoundException(AppException):
    """Resource not found exception"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str = None,
        resource_id: str = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message,
            "NOT_FOUND",
            status.HTTP_404_NOT_FOUND,
            details
        )

class ConflictException(AppException):
    """Resource conflict exception"""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        conflicting_field: str = None,
        details: Dict[str, Any] = None
    ):
        if conflicting_field:
            details = details or {}
            details["conflicting_field"] = conflicting_field
        
        super().__init__(
            message,
            "CONFLICT",
            status.HTTP_409_CONFLICT,
            details
        )

class AuthenticationException(AppException):
    """Authentication failure exception"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message,
            "AUTHENTICATION_FAILED",
            status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationException(AppException):
    """Authorization failure exception"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message,
            "ACCESS_DENIED",
            status.HTTP_403_FORBIDDEN
        )

class RateLimitException(AppException):
    """Rate limit exceeded exception"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message,
            "RATE_LIMIT_EXCEEDED",
            status.HTTP_429_TOO_MANY_REQUESTS
        )

class DatabaseException(AppException):
    """Database operation exception"""
    
    def __init__(self, message: str, original_error: Exception = None):
        details = {}
        if original_error:
            details["original_error"] = str(original_error)
        
        super().__init__(
            message,
            "DATABASE_ERROR",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            details
        )

class ExternalServiceException(AppException):
    """External service error exception"""
    
    def __init__(
        self,
        message: str,
        service_name: str = None,
        status_code: int = status.HTTP_502_BAD_GATEWAY
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        
        super().__init__(
            message,
            "EXTERNAL_SERVICE_ERROR",
            status_code,
            details
        )

def create_error_response(
    message: str,
    error_code: str = "ERROR",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Dict[str, Any] = None,
    errors: List[ErrorDetail] = None
) -> JSONResponse:
    """
    Create standardized error response
    
    Args:
        message: Error message
        error_code: Error code
        status_code: HTTP status code
        details: Additional error details
        errors: Validation errors
        
    Returns:
        JSON error response
    """
    error_data = {
        "detail": message,
        "status_code": status_code,
        "timestamp": datetime.utcnow(),
        "error_code": error_code
    }
    
    if details:
        error_data["details"] = details
    
    if errors:
        error_data["errors"] = [error.dict() for error in errors]
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )

def log_exception(
    request: Request,
    exc: Exception,
    status_code: int = None
) -> None:
    """
    Log exception with request context
    
    Args:
        request: FastAPI request object
        exc: Exception that occurred
        status_code: HTTP status code
    """
    # Extract request information
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client": getattr(request, "client", None),
        "headers": dict(request.headers) if hasattr(request, "headers") else {}
    }
    
    # Log exception with context
    logger.error(
        f"Exception in {request.method} {request.url.path}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "status_code": status_code,
            "request": request_info,
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions
    
    Args:
        request: FastAPI request object
        exc: Application exception
        
    Returns:
        JSON error response
    """
    log_exception(request, exc, exc.status_code)
    
    return create_error_response(
        message=exc.message,
        error_code=exc.error_code,
        status_code=exc.status_code,
        details=exc.details
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSON error response
    """
    log_exception(request, exc, exc.status_code)
    
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return create_error_response(
        message=exc.detail,
        error_code=error_code,
        status_code=exc.status_code
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation exceptions
    
    Args:
        request: FastAPI request object
        exc: Validation exception
        
    Returns:
        JSON error response with validation details
    """
    log_exception(request, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    # Convert validation errors to ErrorDetail objects
    errors = []
    for error in exc.errors():
        errors.append(ErrorDetail(
            type=error["type"],
            msg=error["msg"],
            loc=error.get("loc", [])
        ))
    
    return create_error_response(
        message="Validation error",
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        errors=errors
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database exceptions
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy exception
        
    Returns:
        JSON error response
    """
    log_exception(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Map specific SQLAlchemy exceptions
    if isinstance(exc, IntegrityError):
        if "UNIQUE constraint failed" in str(exc) or "duplicate key" in str(exc):
            return create_error_response(
                message="Duplicate entry - resource already exists",
                error_code="DUPLICATE_ENTRY",
                status_code=status.HTTP_409_CONFLICT,
                details={"database_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)}
            )
        elif "FOREIGN KEY constraint failed" in str(exc):
            return create_error_response(
                message="Invalid reference - related resource not found",
                error_code="INVALID_REFERENCE",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details={"database_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)}
            )
        else:
            return create_error_response(
                message="Data integrity constraint violation",
                error_code="INTEGRITY_ERROR",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details={"database_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)}
            )
    
    elif isinstance(exc, OperationalError):
        return create_error_response(
            message="Database connection or operation error",
            error_code="DATABASE_OPERATION_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"database_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)}
        )
    
    # Generic database error
    return create_error_response(
        message="Database error occurred",
        error_code="DATABASE_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"database_error": str(exc)}
    )

async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic validation exceptions
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation exception
        
    Returns:
        JSON error response with validation details
    """
    log_exception(request, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    # Convert Pydantic errors to ErrorDetail objects
    errors = []
    for error in exc.errors():
        errors.append(ErrorDetail(
            type=error["type"],
            msg=error["msg"],
            loc=error.get("loc", [])
        ))
    
    return create_error_response(
        message="Data validation error",
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        errors=errors
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions
    
    Args:
        request: FastAPI request object
        exc: Generic exception
        
    Returns:
        JSON error response
    """
    log_exception(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Don't expose internal error details in production
    import os
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    if debug_mode:
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc()
        }
    else:
        details = None
    
    return create_error_response(
        message="An unexpected error occurred",
        error_code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details
    )

def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationException, app_exception_handler)
    app.add_exception_handler(NotFoundException, app_exception_handler)
    app.add_exception_handler(ConflictException, app_exception_handler)
    app.add_exception_handler(AuthenticationException, app_exception_handler)
    app.add_exception_handler(AuthorizationException, app_exception_handler)
    app.add_exception_handler(RateLimitException, app_exception_handler)
    app.add_exception_handler(DatabaseException, app_exception_handler)
    app.add_exception_handler(ExternalServiceException, app_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Database exceptions
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")

# Export exception classes and handlers
__all__ = [
    # Exception classes
    "AppException",
    "ValidationException",
    "NotFoundException",
    "ConflictException",
    "AuthenticationException",
    "AuthorizationException",
    "RateLimitException",
    "DatabaseException",
    "ExternalServiceException",
    
    # Handler functions
    "create_error_response",
    "log_exception",
    "register_exception_handlers",
    
    # Individual handlers
    "app_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "sqlalchemy_exception_handler",
    "pydantic_validation_exception_handler",
    "generic_exception_handler"
]