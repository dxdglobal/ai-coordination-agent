"""
Central logging and error tracking for Task Management AI System
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
import json

class TaskManagementLogger:
    """Centralized logger for the task management system"""
    
    def __init__(self, log_level: str = 'INFO', log_file: str = None):
        self.log_level = log_level.upper()
        self.log_file = log_file or os.path.join(os.path.dirname(__file__), '..', 'logs', 'task_management.log')
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Configure logger
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file and console handlers"""
        logger = logging.getLogger('task_management')
        logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(getattr(logging, self.log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, extra_data: Dict[str, Any] = None):
        """Log info message"""
        log_message = self._format_message(message, extra_data)
        self.logger.info(log_message)
    
    def warning(self, message: str, extra_data: Dict[str, Any] = None):
        """Log warning message"""
        log_message = self._format_message(message, extra_data)
        self.logger.warning(log_message)
    
    def error(self, message: str, error: Exception = None, extra_data: Dict[str, Any] = None):
        """Log error message with optional exception details"""
        log_data = extra_data or {}
        
        if error:
            log_data.update({
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc()
            })
        
        log_message = self._format_message(message, log_data)
        self.logger.error(log_message)
    
    def debug(self, message: str, extra_data: Dict[str, Any] = None):
        """Log debug message"""
        log_message = self._format_message(message, extra_data)
        self.logger.debug(log_message)
    
    def _format_message(self, message: str, extra_data: Dict[str, Any] = None) -> str:
        """Format log message with additional data"""
        if extra_data:
            return f"{message} | Data: {json.dumps(extra_data, default=str)}"
        return message
    
    def log_db_operation(self, operation: str, table: str, success: bool, 
                        execution_time: float = None, rows_affected: int = None):
        """Log database operation"""
        log_data = {
            'operation': operation,
            'table': table,
            'success': success,
            'execution_time_ms': execution_time * 1000 if execution_time else None,
            'rows_affected': rows_affected
        }
        
        if success:
            self.info(f"DB Operation: {operation} on {table}", log_data)
        else:
            self.error(f"DB Operation Failed: {operation} on {table}", extra_data=log_data)
    
    def log_openai_request(self, model: str, tokens_used: int, 
                          response_time: float, success: bool, error: str = None):
        """Log OpenAI API request"""
        log_data = {
            'model': model,
            'tokens_used': tokens_used,
            'response_time_ms': response_time * 1000,
            'success': success,
            'error': error
        }
        
        if success:
            self.info(f"OpenAI Request: {model}", log_data)
        else:
            self.error(f"OpenAI Request Failed: {model}", extra_data=log_data)
    
    def log_embedding_operation(self, operation: str, texts_count: int, 
                               success: bool, execution_time: float = None):
        """Log embedding operation"""
        log_data = {
            'operation': operation,
            'texts_count': texts_count,
            'success': success,
            'execution_time_ms': execution_time * 1000 if execution_time else None
        }
        
        if success:
            self.info(f"Embedding Operation: {operation}", log_data)
        else:
            self.error(f"Embedding Operation Failed: {operation}", extra_data=log_data)
    
    def log_nlp_processing(self, query: str, intent: str, employee: str, 
                          confidence: float, processing_time: float):
        """Log NLP processing results"""
        log_data = {
            'query_length': len(query),
            'intent': intent,
            'employee': employee,
            'confidence': confidence,
            'processing_time_ms': processing_time * 1000
        }
        
        self.info("NLP Processing completed", log_data)
    
    def log_performance_metrics(self, endpoint: str, response_time: float, 
                               status_code: int, user_id: str = None):
        """Log API performance metrics"""
        log_data = {
            'endpoint': endpoint,
            'response_time_ms': response_time * 1000,
            'status_code': status_code,
            'user_id': user_id
        }
        
        if status_code < 400:
            self.info(f"API Request: {endpoint}", log_data)
        else:
            self.warning(f"API Request Error: {endpoint}", log_data)

# Global logger instance
logger = TaskManagementLogger()

def get_logger() -> TaskManagementLogger:
    """Get the global logger instance"""
    return logger

# Convenience functions
def log_info(message: str, extra_data: Dict[str, Any] = None):
    logger.info(message, extra_data)

def log_warning(message: str, extra_data: Dict[str, Any] = None):
    logger.warning(message, extra_data)

def log_error(message: str, error: Exception = None, extra_data: Dict[str, Any] = None):
    logger.error(message, error, extra_data)

def log_debug(message: str, extra_data: Dict[str, Any] = None):
    logger.debug(message, extra_data)