"""
Tasks Controller
Handles task-related business logic and database operations from CRM                task = {
                    'id': raw_task['id'],
                    'title': raw_task.get('title', 'Untitled Task'),
                    'description': raw_task.get('description', ''),
                    'status': mapped_status,  # Use the mapped status we calculated above
                    'priority': priority_map.get(raw_task['priority'], 'medium'),ase
"""

import os
import mysql.connector
from flask import jsonify
from datetime import datetime

class TaskController:
    def __init__(self):
        pass
    
    def get_database_connection(self):
        """Get MySQL database connection"""
        try:
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=int(os.getenv('DB_PORT', 3306))
            )
            return connection
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def get_all_tasks(self):
        """Fetch all tasks from CRM database"""
        connection = self.get_database_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Query to get all tasks with project info
            query = """
            SELECT 
                t.id,
                t.name as title,
                t.description,
                t.status,
                t.priority,
                t.startdate as start_time,
                t.duedate as end_time,
                t.milestone,
                t.kanban_order,
                t.billable,
                t.billed,
                t.rel_id as project_id,
                t.rel_type,
                t.dateadded as created_at,
                t.addedfrom as created_by,
                t.datefinished as finished_at,
                p.name as project_name,
                ta.firstname as assignee_firstname,
                ta.lastname as assignee_lastname,
                CONCAT(ta.firstname, ' ', ta.lastname) as assignee
            FROM tbltasks t
            LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
            LEFT JOIN tblstaff ta ON t.addedfrom = ta.staffid
            ORDER BY t.id DESC
            """
            
            cursor.execute(query)
            raw_tasks = cursor.fetchall()
            
            tasks = []
            for raw_task in raw_tasks:
                # Map status numbers to readable text
                status_map = {
                    1: 'todo',
                    2: 'in_progress', 
                    3: 'review',
                    4: 'done',
                    5: 'done'  # Completed
                }
                
                # Map priority numbers to readable text
                priority_map = {
                    1: 'low',
                    2: 'medium',
                    3: 'high',
                    4: 'urgent'
                }
                
                task = {
                    'id': raw_task['id'],
                    'title': raw_task['title'] or 'Untitled Task',
                    'description': raw_task.get('description', ''),
                    'status': status_map.get(raw_task['status'], 'todo'),
                    'priority': priority_map.get(raw_task['priority'], 'medium'),
                    'assignee': raw_task.get('assignee', '').strip() if raw_task.get('assignee') else None,
                    'project_id': raw_task.get('project_id'),
                    'project_name': raw_task.get('project_name'),
                    'milestone': raw_task.get('milestone'),
                    'billable': bool(raw_task.get('billable', 0)),
                    'billed': bool(raw_task.get('billed', 0)),
                    'kanban_order': raw_task.get('kanban_order', 0),
                    'estimated_hours': 0,  # Default value, can be calculated if needed
                    'actual_hours': 0,     # Default value, can be calculated if needed
                    'start_time': None,
                    'end_time': None,
                    'created_at': None,
                    'finished_at': None
                }
                
                # Convert dates
                if raw_task.get('start_time'):
                    task['start_time'] = raw_task['start_time'].strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(raw_task['start_time'], 'strftime') else str(raw_task['start_time'])
                    
                if raw_task.get('end_time'):
                    task['end_time'] = raw_task['end_time'].strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(raw_task['end_time'], 'strftime') else str(raw_task['end_time'])
                    
                if raw_task.get('created_at'):
                    task['created_at'] = raw_task['created_at'].strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(raw_task['created_at'], 'strftime') else str(raw_task['created_at'])
                    
                if raw_task.get('finished_at'):
                    task['finished_at'] = raw_task['finished_at'].strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(raw_task['finished_at'], 'strftime') else str(raw_task['finished_at'])
                
                tasks.append(task)
            
            return jsonify({
                'success': True,
                'tasks': tasks,
                'total_count': len(tasks),
                'message': f'Found {len(tasks)} tasks'
            }), 200
            
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            return jsonify({'error': f'Failed to fetch tasks: {str(e)}'}), 500
        finally:
            if connection:
                connection.close()
    
    def search_tasks(self, filters=None):
        """Search tasks with various filters"""
        connection = self.get_database_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Base query
            query = """
            SELECT 
                t.id,
                t.name as title,
                t.description,
                t.status,
                t.priority,
                t.startdate as start_time,
                t.duedate as end_time,
                t.milestone,
                t.kanban_order,
                t.billable,
                t.billed,
                t.rel_id as project_id,
                t.rel_type,
                t.dateadded as created_at,
                t.addedfrom as created_by,
                t.datefinished as finished_at,
                p.name as project_name,
                ta.firstname as assignee_firstname,
                ta.lastname as assignee_lastname,
                CONCAT(ta.firstname, ' ', ta.lastname) as assignee
            FROM tbltasks t
            LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
            LEFT JOIN tblstaff ta ON t.addedfrom = ta.staffid
            WHERE 1=1
            """
            
            params = []
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    status_param = filters['status']
                    if status_param == 'active' or 'not_started,todo,in_progress,review' in status_param:
                        # Handle active tasks (not_started, todo, in_progress, review)
                        query += " AND t.status IN (0, 1, 2, 3)"
                    elif status_param == 'overdue':
                        # Handle overdue tasks - get all tasks with past due dates, filter out done tasks later
                        query += " AND DATE(t.duedate) < CURDATE() AND t.duedate IS NOT NULL"
                    else:
                        # Map status names to numbers
                        status_reverse_map = {
                            'not_started': 0,
                            'todo': 1,
                            'in_progress': 2,
                            'review': 3,
                            'done': 4,
                            'completed': 5
                        }
                        status_num = status_reverse_map.get(status_param)
                        if status_num:
                            query += " AND t.status = %s"
                            params.append(status_num)
                
                if filters.get('priority'):
                    # Map priority names to numbers
                    priority_reverse_map = {
                        'low': 1,
                        'medium': 2,
                        'high': 3,
                        'urgent': 4
                    }
                    priority_num = priority_reverse_map.get(filters['priority'])
                    if priority_num:
                        query += " AND t.priority = %s"
                        params.append(priority_num)
                
                if filters.get('project_id'):
                    query += " AND t.rel_id = %s"
                    params.append(filters['project_id'])
                
                if filters.get('title'):
                    query += " AND (t.name LIKE %s OR t.description LIKE %s)"
                    search_term = f"%{filters['title']}%"
                    params.extend([search_term, search_term])
                
                if filters.get('assignee'):
                    query += " AND CONCAT(ta.firstname, ' ', ta.lastname) LIKE %s"
                    params.append(f"%{filters['assignee']}%")
            
            # Add sorting
            sort_by = filters.get('sort_by', 'id') if filters else 'id'
            sort_order = filters.get('sort_order', 'DESC') if filters else 'DESC'
            
            # Validate sort_by to prevent SQL injection
            valid_sort_columns = ['id', 'title', 'status', 'priority', 'startdate', 'duedate', 'dateadded']
            if sort_by.replace('t.', '') in valid_sort_columns:
                if not sort_by.startswith('t.'):
                    sort_by = f't.{sort_by}'
                query += f" ORDER BY {sort_by} {sort_order}"
            else:
                query += " ORDER BY t.id DESC"
            
            # Add pagination
            limit = filters.get('limit', 50) if filters else 50
            offset = filters.get('offset', 0) if filters else 0
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
                
            if offset:
                query += " OFFSET %s"
                params.append(offset)
            
            cursor.execute(query, params)
            raw_tasks = cursor.fetchall()
            
            tasks = []
            # Apply post-processing filters after status mapping
            tasks = []
            for raw_task in raw_tasks:
                # Map status numbers to readable text
                status_map = {
                    1: 'todo',
                    2: 'in_progress', 
                    3: 'review',
                    4: 'done',
                    5: 'done',
                    0: 'not_started'  # Add not started status
                }
                
                # Map priority numbers to readable text
                priority_map = {
                    1: 'low',
                    2: 'medium',
                    3: 'high',
                    4: 'urgent'
                }
                
                # Get mapped status
                mapped_status = status_map.get(raw_task['status'], 'todo')
                
                # For overdue filter, exclude done tasks at this stage
                if filters and filters.get('status') == 'overdue':
                    if mapped_status == 'done':
                        continue  # Skip done tasks for overdue filter
                
                task = {
                    'id': raw_task['id'],
                    'title': raw_task['title'] or 'Untitled Task',
                    'description': raw_task.get('description', ''),
                    'status': status_map.get(raw_task['status'], 'todo'),
                    'priority': priority_map.get(raw_task['priority'], 'medium'),
                    'assignee': raw_task.get('assignee', '').strip() if raw_task.get('assignee') else None,
                    'project_id': raw_task.get('project_id'),
                    'project_name': raw_task.get('project_name'),
                    'milestone': raw_task.get('milestone'),
                    'billable': bool(raw_task.get('billable', 0)),
                    'billed': bool(raw_task.get('billed', 0)),
                    'kanban_order': raw_task.get('kanban_order', 0),
                    'estimated_hours': 0,
                    'actual_hours': 0,
                    'start_time': None,
                    'end_time': None,
                    'created_at': None,
                    'finished_at': None
                }
                
                # Convert dates
                if raw_task.get('start_time'):
                    task['start_time'] = raw_task['start_time'].strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(raw_task['start_time'], 'strftime') else str(raw_task['start_time'])
                    
                if raw_task.get('end_time'):
                    task['end_time'] = raw_task['end_time'].strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(raw_task['end_time'], 'strftime') else str(raw_task['end_time'])
                    
                if raw_task.get('created_at'):
                    task['created_at'] = raw_task['created_at'].strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(raw_task['created_at'], 'strftime') else str(raw_task['created_at'])
                    
                if raw_task.get('finished_at'):
                    task['finished_at'] = raw_task['finished_at'].strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(raw_task['finished_at'], 'strftime') else str(raw_task['finished_at'])
                
                tasks.append(task)
            
            return jsonify({
                'success': True,
                'tasks': tasks,
                'total': len(tasks),
                'limit': limit,
                'offset': offset
            }), 200
            
        except Exception as e:
            print(f"Error searching tasks: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to search tasks: {str(e)}',
                'tasks': [],
                'total': 0
            }), 500
        finally:
            if connection:
                connection.close()
    
    def get_task_stats(self):
        """Get task statistics"""
        connection = self.get_database_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get all tasks for statistics
            query = """
            SELECT 
                t.status,
                t.priority,
                t.duedate,
                t.datefinished
            FROM tbltasks t
            """
            
            cursor.execute(query)
            raw_tasks = cursor.fetchall()
            
            # Calculate statistics
            stats = {
                "total_tasks": len(raw_tasks),
                "tasks_by_status": {},
                "tasks_by_priority": {},
                "active_tasks": 0,
                "completed_tasks": 0,
                "overdue_tasks": 0
            }
            
            status_map = {
                1: 'todo',
                2: 'in_progress', 
                3: 'review',
                4: 'done',
                5: 'done',
                0: 'not_started'  # Add not started status
            }
            
            priority_map = {
                1: 'low',
                2: 'medium',
                3: 'high',
                4: 'urgent'
            }
            
            for task in raw_tasks:
                # Status counts
                status = status_map.get(task['status'], 'unknown')
                stats["tasks_by_status"][status] = stats["tasks_by_status"].get(status, 0) + 1
                
                # Priority counts  
                priority = priority_map.get(task['priority'], 'unknown')
                stats["tasks_by_priority"][priority] = stats["tasks_by_priority"].get(priority, 0) + 1
                
                # Active tasks (not done - includes not_started, todo, in_progress, review)
                if task['status'] not in [4, 5]:
                    stats["active_tasks"] += 1
                
                # Completed tasks
                if task['status'] in [4, 5]:
                    stats["completed_tasks"] += 1
                
                # Overdue tasks (due date passed and not completed)
                if (task.get('duedate') and 
                    task['duedate'] and
                    task['status'] not in [4, 5]):
                    try:
                        # Convert date to datetime for comparison if needed
                        due_date = task['duedate']
                        if hasattr(due_date, 'date'):
                            # It's already a datetime, get the date part
                            due_date = due_date.date()
                        
                        current_date = datetime.now().date()
                        
                        if due_date < current_date:
                            stats["overdue_tasks"] += 1
                    except (TypeError, AttributeError):
                        # Skip if date comparison fails
                        pass
            
            return jsonify({
                "success": True,
                "stats": stats
            }), 200
            
        except Exception as e:
            print(f"Error getting task statistics: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to get task statistics: {str(e)}",
                "stats": {}
            }), 500
        finally:
            if connection:
                connection.close()
    
    def get_task_by_id(self, task_id):
        """Get a specific task by ID"""
        connection = self.get_database_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT 
                t.*,
                p.name as project_name,
                ta.firstname as assignee_firstname,
                ta.lastname as assignee_lastname,
                CONCAT(ta.firstname, ' ', ta.lastname) as assignee
            FROM tbltasks t
            LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
            LEFT JOIN tblstaff ta ON t.addedfrom = ta.staffid
            WHERE t.id = %s
            """
            
            cursor.execute(query, (task_id,))
            raw_task = cursor.fetchone()
            
            if not raw_task:
                return jsonify({'error': 'Task not found'}), 404
            
            # Format the task
            status_map = {
                1: 'todo',
                2: 'in_progress', 
                3: 'review',
                4: 'done',
                5: 'done'
            }
            
            priority_map = {
                1: 'low',
                2: 'medium',
                3: 'high',
                4: 'urgent'
            }
            
            task = {
                'id': raw_task['id'],
                'title': raw_task['name'] or 'Untitled Task',
                'description': raw_task.get('description', ''),
                'status': status_map.get(raw_task['status'], 'todo'),
                'priority': priority_map.get(raw_task['priority'], 'medium'),
                'assignee': raw_task.get('assignee', '').strip() if raw_task.get('assignee') else None,
                'project_id': raw_task.get('rel_id'),
                'project_name': raw_task.get('project_name'),
                'milestone': raw_task.get('milestone'),
                'billable': bool(raw_task.get('billable', 0)),
                'billed': bool(raw_task.get('billed', 0)),
                'kanban_order': raw_task.get('kanban_order', 0)
            }
            
            return jsonify({
                'success': True,
                'task': task
            }), 200
            
        except Exception as e:
            print(f"Error fetching task: {e}")
            return jsonify({'error': f'Failed to fetch task: {str(e)}'}), 500
        finally:
            if connection:
                connection.close()