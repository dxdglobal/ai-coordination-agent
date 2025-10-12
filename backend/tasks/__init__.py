"""
Task Management Module

This module provides comprehensive task management functionality including:
- Task data retrieval and analysis
- Employee task performance tracking
- Task status management
- Task assignment and scheduling
- Task reporting and analytics
"""

from .services.task_service import TaskService
from .services.employee_task_analyzer import EmployeeTaskAnalyzer
from .utils.task_mapper import TaskStatusMapper, TaskPriorityMapper

__all__ = [
    'TaskService',
    'EmployeeTaskAnalyzer', 
    'TaskStatusMapper',
    'TaskPriorityMapper'
]