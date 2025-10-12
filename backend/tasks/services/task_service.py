"""
Core Task Service

Main service for task operations including CRUD operations,
task assignment, status updates, and task management.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from tasks.utils.task_mapper import TaskStatusMapper, TaskPriorityMapper
from core.crm.real_crm_server import get_database_connection


class TaskService:
    """Core task management service"""
    
    def __init__(self):
        self.status_mapper = TaskStatusMapper()
        self.priority_mapper = TaskPriorityMapper()
    
    def get_task_by_id(self, task_id: int) -> Dict[str, Any]:
        """Get a specific task by ID"""
        try:
            connection = get_database_connection()
            if not connection:
                return {'success': False, 'error': 'Database connection failed'}
            
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT 
                t.id as task_id,
                t.name as task_name,
                t.description,
                t.status,
                t.priority,
                t.startdate,
                t.duedate,
                t.datefinished,
                t.dateadded,
                p.name as project_name,
                c.company as client_name
            FROM tbltasks t
            LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
            LEFT JOIN tblclients c ON p.clientid = c.userid
            WHERE t.id = %s
            """
            
            cursor.execute(query, (task_id,))
            task = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            if not task:
                return {'success': False, 'error': f'Task {task_id} not found'}
            
            # Standardize task format
            standardized_task = {
                'id': task['task_id'],
                'title': task['task_name'],
                'description': task['description'],
                'status': self.status_mapper.map_status(task['status']),
                'priority': self.priority_mapper.map_priority(task['priority']),
                'start_date': task['startdate'],
                'due_date': task['duedate'],
                'finished_date': task['datefinished'],
                'created_date': task['dateadded'],
                'project_name': task['project_name'],
                'client_name': task['client_name']
            }
            
            return {'success': True, 'task': standardized_task}
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to get task: {str(e)}'}
    
    def get_tasks_by_status(self, status: str) -> Dict[str, Any]:
        """Get all tasks with a specific status"""
        try:
            # Map status string back to ID
            status_id = None
            for id, mapped_status in self.status_mapper.get_all_statuses().items():
                if mapped_status == status:
                    status_id = id
                    break
            
            if status_id is None:
                return {'success': False, 'error': f'Invalid status: {status}'}
            
            connection = get_database_connection()
            if not connection:
                return {'success': False, 'error': 'Database connection failed'}
            
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT 
                t.id as task_id,
                t.name as task_name,
                t.description,
                t.status,
                t.priority,
                t.startdate,
                t.duedate,
                t.dateadded,
                p.name as project_name,
                s.firstname,
                s.lastname
            FROM tbltasks t
            LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
            LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
            LEFT JOIN tblstaff s ON ta.staffid = s.staffid
            WHERE t.status = %s
            ORDER BY t.dateadded DESC
            """
            
            cursor.execute(query, (status_id,))
            tasks = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            # Standardize tasks
            standardized_tasks = []
            for task in tasks:
                standardized_task = {
                    'id': task['task_id'],
                    'title': task['task_name'],
                    'description': task['description'],
                    'status': self.status_mapper.map_status(task['status']),
                    'priority': self.priority_mapper.map_priority(task['priority']),
                    'start_date': task['startdate'],
                    'due_date': task['duedate'],
                    'created_date': task['dateadded'],
                    'project_name': task['project_name'],
                    'assignee': f"{task.get('firstname', '')} {task.get('lastname', '')}".strip()
                }
                standardized_tasks.append(standardized_task)
            
            return {
                'success': True,
                'tasks': standardized_tasks,
                'total': len(standardized_tasks),
                'status': status
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to get tasks by status: {str(e)}'}
    
    def get_overdue_tasks(self) -> Dict[str, Any]:
        """Get all overdue tasks"""
        try:
            connection = get_database_connection()
            if not connection:
                return {'success': False, 'error': 'Database connection failed'}
            
            cursor = connection.cursor(dictionary=True)
            
            # Get tasks that are overdue (due date passed and not completed)
            query = """
            SELECT 
                t.id as task_id,
                t.name as task_name,
                t.description,
                t.status,
                t.priority,
                t.startdate,
                t.duedate,
                t.dateadded,
                p.name as project_name,
                s.firstname,
                s.lastname,
                DATEDIFF(CURDATE(), t.duedate) as days_overdue
            FROM tbltasks t
            LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
            LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
            LEFT JOIN tblstaff s ON ta.staffid = s.staffid
            WHERE t.duedate < CURDATE() 
            AND t.status != 5
            AND t.duedate IS NOT NULL
            ORDER BY t.duedate ASC
            """
            
            cursor.execute(query)
            tasks = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            # Standardize tasks
            overdue_tasks = []
            for task in tasks:
                standardized_task = {
                    'id': task['task_id'],
                    'title': task['task_name'],
                    'description': task['description'],
                    'status': self.status_mapper.map_status(task['status']),
                    'priority': self.priority_mapper.map_priority(task['priority']),
                    'start_date': task['startdate'],
                    'due_date': task['duedate'],
                    'created_date': task['dateadded'],
                    'project_name': task['project_name'],
                    'assignee': f"{task.get('firstname', '')} {task.get('lastname', '')}".strip(),
                    'days_overdue': task['days_overdue']
                }
                overdue_tasks.append(standardized_task)
            
            return {
                'success': True,
                'tasks': overdue_tasks,
                'total': len(overdue_tasks)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to get overdue tasks: {str(e)}'}
    
    def update_task_status(self, task_id: int, new_status: str) -> Dict[str, Any]:
        """Update task status"""
        try:
            # Map status string to ID
            status_id = None
            for id, mapped_status in self.status_mapper.get_all_statuses().items():
                if mapped_status == new_status:
                    status_id = id
                    break
            
            if status_id is None:
                return {'success': False, 'error': f'Invalid status: {new_status}'}
            
            connection = get_database_connection()
            if not connection:
                return {'success': False, 'error': 'Database connection failed'}
            
            cursor = connection.cursor()
            
            # Update task status
            update_query = "UPDATE tbltasks SET status = %s WHERE id = %s"
            cursor.execute(update_query, (status_id, task_id))
            
            # If marking as done, set finish date
            if new_status == 'done':
                finish_query = "UPDATE tbltasks SET datefinished = NOW() WHERE id = %s"
                cursor.execute(finish_query, (task_id,))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {
                'success': True,
                'message': f'Task {task_id} status updated to {new_status}'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to update task status: {str(e)}'}


# Global instance
task_service = TaskService()