"""
Logging Configuration - Task 1.3
=================================

Comprehensive logging configuration for the AI Coordination Agent backend.
Provides structured logging with different handlers, formatters, and levels.

Features:
- Structured JSON logging for production
- Console logging for development
- File rotation and retention
- Request/response logging
- Error tracking and monitoring
- Performance logging

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import os
import sys
import logging
import logging.config
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or text
LOG_DIR = os.getenv("LOG_DIR", "logs")
APP_NAME = os.getenv("APP_NAME", "ai-coordination-agent")

# Ensure log directory exists
Path(LOG_DIR).mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'lineno', 'funcName', 'created', 
                'msecs', 'relativeCreated', 'thread', 'threadName', 
                'processName', 'process', 'getMessage', 'exc_info', 
                'exc_text', 'stack_info'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # Create colored level name
        colored_level = f"{level_color}{record.levelname}{reset_color}"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build log message
        message = f"{timestamp} | {colored_level:20s} | {record.name:25s} | {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message

def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration dictionary
    
    Returns:
        Logging configuration for dictConfig
    """
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "text": {
                "()": ColoredFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": LOG_LEVEL,
                "formatter": "text" if LOG_FORMAT == "text" else "json",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": LOG_LEVEL,
                "formatter": "json",
                "filename": os.path.join(LOG_DIR, f"{APP_NAME}.log"),
                "maxBytes": 50 * 1024 * 1024,  # 50MB
                "backupCount": 10,
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": os.path.join(LOG_DIR, f"{APP_NAME}-errors.log"),
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": os.path.join(LOG_DIR, f"{APP_NAME}-access.log"),
                "maxBytes": 100 * 1024 * 1024,  # 100MB
                "backupCount": 20,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            # FastAPI access logs
            "uvicorn.access": {
                "handlers": ["access_file"],
                "level": "INFO",
                "propagate": False
            },
            # Application loggers
            "app": {
                "handlers": ["console", "file", "error_file"],
                "level": LOG_LEVEL,
                "propagate": False
            },
            "services": {
                "handlers": ["console", "file", "error_file"],
                "level": LOG_LEVEL,
                "propagate": False
            },
            "database": {
                "handlers": ["console", "file", "error_file"],
                "level": LOG_LEVEL,
                "propagate": False
            },
            "routes": {
                "handlers": ["console", "file", "error_file"],
                "level": LOG_LEVEL,
                "propagate": False
            },
            # SQLAlchemy logs
            "sqlalchemy.engine": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False
            },
            "sqlalchemy.pool": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False
            },
            # External library logs
            "urllib3": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False
            },
            "requests": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False
            }
        },
        "root": {
            "level": LOG_LEVEL,
            "handlers": ["console", "file", "error_file"]
        }
    }
    
    return config

def setup_logging():
    """Initialize logging configuration"""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger("app")
    logger.info(
        "Logging initialized",
        extra={
            "log_level": LOG_LEVEL,
            "log_format": LOG_FORMAT,
            "log_dir": LOG_DIR,
            "app_name": APP_NAME
        }
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for a module
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("routes.middleware")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = datetime.utcnow()
        request_id = f"req_{start_time.timestamp():.6f}"
        
        # Log request
        self.logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": scope["method"],
                "path": scope["path"],
                "query_string": scope["query_string"].decode(),
                "client": scope.get("client"),
                "headers": dict(scope.get("headers", []))
            }
        )
        
        # Capture response
        status_code = None
        response_headers = {}
        
        async def send_wrapper(message):
            nonlocal status_code, response_headers
            
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = dict(message.get("headers", []))
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            
            # Log response
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": status_code,
                    "duration_seconds": duration,
                    "response_headers": response_headers
                }
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration_seconds": duration
                },
                exc_info=True
            )
            raise

class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, operation: str, logger: Optional[logging.Logger] = None):
        self.operation = operation
        self.logger = logger or get_logger("app.performance")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.debug(f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation}",
                extra={
                    "operation": self.operation,
                    "duration_seconds": duration,
                    "success": True
                }
            )
        else:
            self.logger.error(
                f"Failed {self.operation}",
                extra={
                    "operation": self.operation,
                    "duration_seconds": duration,
                    "success": False,
                    "error": str(exc_val)
                },
                exc_info=True
            )

def log_function_call(func):
    """Decorator for logging function calls"""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        logger.debug(
            f"Function call: {func_name}",
            extra={
                "function": func_name,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
        )
        
        try:
            with PerformanceLogger(func_name, logger):
                result = func(*args, **kwargs)
            
            logger.debug(f"Function completed: {func_name}")
            return result
            
        except Exception as e:
            logger.error(
                f"Function failed: {func_name}",
                extra={
                    "function": func_name,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    return wrapper

def log_async_function_call(func):
    """Decorator for logging async function calls"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        logger.debug(
            f"Async function call: {func_name}",
            extra={
                "function": func_name,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
        )
        
        try:
            with PerformanceLogger(func_name, logger):
                result = await func(*args, **kwargs)
            
            logger.debug(f"Async function completed: {func_name}")
            return result
            
        except Exception as e:
            logger.error(
                f"Async function failed: {func_name}",
                extra={
                    "function": func_name,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    return wrapper

# Initialize logging on import
setup_logging()

# Export logging utilities
__all__ = [
    "setup_logging",
    "get_logger",
    "RequestLoggingMiddleware",
    "PerformanceLogger",
    "log_function_call",
    "log_async_function_call",
    "JSONFormatter",
    "ColoredFormatter"
]