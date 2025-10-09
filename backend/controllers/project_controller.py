"""
Projects Controller
Handles project-related business logic and database operations
"""

import os
import mysql.connector
from flask import jsonify
from datetime import datetime

class ProjectController:
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
    
    def get_all_projects(self):
        """Fetch all projects from CRM database"""
        connection = self.get_database_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Query to get all projects with basic info
            query = """
            SELECT 
                p.id,
                p.name,
                p.description,
                p.status,
                p.start_date,
                p.deadline,
                p.project_created,
                p.progress,
                p.project_cost,
                p.project_rate_per_hour,
                p.estimated_hours
            FROM tblprojects p
            ORDER BY p.id DESC
            """
            
            cursor.execute(query)
            raw_projects = cursor.fetchall()
            
            projects = []
            for raw_project in raw_projects:
                # Map status numbers to readable text
                status_map = {
                    1: 'Not Started',
                    2: 'In Progress', 
                    3: 'On Hold',
                    4: 'Cancelled',
                    5: 'Finished'
                }
                
                project = {
                    'id': raw_project['id'],
                    'name': raw_project['name'],
                    'description': raw_project.get('description', ''),
                    'status': status_map.get(raw_project['status'], 'Unknown'),
                    'status_id': raw_project['status'],
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'active_tasks': 0,
                    'progress': raw_project.get('progress', 0) or 0,
                    'estimated_hours': raw_project.get('estimated_hours', 0) or 0,
                    'project_cost': float(raw_project.get('project_cost', 0) or 0),
                    'hourly_rate': float(raw_project.get('project_rate_per_hour', 0) or 0),
                    'start_date': None,
                    'deadline': None,
                    'created_at': None,
                    'completion_percentage': raw_project.get('progress', 0) or 0,
                    'is_overdue': False,
                    'days_until_deadline': None
                }
                
                # Convert dates
                if raw_project.get('start_date'):
                    project['start_date'] = raw_project['start_date'].strftime('%Y-%m-%d') if hasattr(raw_project['start_date'], 'strftime') else str(raw_project['start_date'])
                    
                if raw_project.get('deadline'):
                    project['deadline'] = raw_project['deadline'].strftime('%Y-%m-%d') if hasattr(raw_project['deadline'], 'strftime') else str(raw_project['deadline'])
                    
                # Set created_at using the correct column name
                if raw_project.get('project_created'):
                    project['created_at'] = raw_project['project_created'].strftime('%Y-%m-%d') if hasattr(raw_project['project_created'], 'strftime') else str(raw_project['project_created'])
                else:
                    project['created_at'] = None
                
                # Set priority based on status and deadline
                if project['is_overdue']:
                    project['priority'] = 'High'
                elif project['days_until_deadline'] and project['days_until_deadline'] <= 7:
                    project['priority'] = 'Medium'
                else:
                    project['priority'] = 'Low'
                
                projects.append(project)
            
            return jsonify({
                'success': True,
                'projects': projects,
                'total_count': len(projects),
                'message': f'Found {len(projects)} projects'
            }), 200
            
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return jsonify({'error': f'Failed to fetch projects: {str(e)}'}), 500
        finally:
            if connection:
                connection.close()
    
    def get_project_by_id(self, project_id):
        """Fetch a specific project by ID with detailed information"""
        connection = self.get_database_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get project details
            project_query = """
            SELECT 
                p.*,
                COUNT(t.id) as total_tasks,
                SUM(CASE WHEN t.status = 5 THEN 1 ELSE 0 END) as completed_tasks
            FROM tblprojects p
            LEFT JOIN tbltasks t ON p.id = t.rel_id AND t.rel_type = 'project'
            WHERE p.id = ?
            GROUP BY p.id
            """
            
            cursor.execute(project_query, (project_id,))
            project_data = cursor.fetchone()
            
            if not project_data:
                return jsonify({'error': 'Project not found'}), 404
            
            # Get project tasks
            tasks_query = """
            SELECT 
                id, name, description, status, priority, dateadded, duedate, startdate
            FROM tbltasks 
            WHERE rel_type = 'project' AND rel_id = ?
            ORDER BY dateadded DESC
            """
            
            cursor.execute(tasks_query, (project_id,))
            tasks_data = cursor.fetchall()
            
            # Format project data
            status_map = {1: 'Not Started', 2: 'In Progress', 3: 'On Hold', 4: 'Cancelled', 5: 'Finished'}
            
            project = {
                'id': project_data['id'],
                'name': project_data['name'],
                'description': project_data.get('description', ''),
                'status': status_map.get(project_data['status'], 'Unknown'),
                'status_id': project_data['status'],
                'progress': project_data.get('progress', 0),
                'total_tasks': project_data['total_tasks'] or 0,
                'completed_tasks': project_data['completed_tasks'] or 0,
                'estimated_hours': project_data.get('estimated_hours', 0),
                'project_cost': float(project_data.get('project_cost', 0) or 0),
                'hourly_rate': float(project_data.get('project_rate_per_hour', 0) or 0),
                'tasks': []
            }
            
            # Format tasks
            task_status_map = {1: 'Not Started', 2: 'In Progress', 3: 'Testing', 4: 'Awaiting Feedback', 5: 'Complete'}
            task_priority_map = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Urgent'}
            
            for task in tasks_data:
                formatted_task = {
                    'id': task['id'],
                    'name': task['name'],
                    'description': task.get('description', ''),
                    'status': task_status_map.get(task['status'], 'Unknown'),
                    'priority': task_priority_map.get(task['priority'], 'Medium'),
                    'created_at': task['dateadded'].strftime('%Y-%m-%d') if task.get('dateadded') else None,
                    'due_date': task['duedate'].strftime('%Y-%m-%d') if task.get('duedate') else None,
                    'start_date': task['startdate'].strftime('%Y-%m-%d') if task.get('startdate') else None,
                }
                project['tasks'].append(formatted_task)
            
            return jsonify({
                'success': True,
                'project': project
            }), 200
            
        except Exception as e:
            print(f"Error fetching project {project_id}: {e}")
            return jsonify({'error': f'Failed to fetch project: {str(e)}'}), 500
        finally:
            if connection:
                connection.close()

    def search_projects(self, search_params):
        """
        Advanced search for projects with multiple filters
        """
        connection = self.get_database_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        try:
            cursor = connection.cursor(dictionary=True)
            
            # Base query with comprehensive data
            base_query = """
            SELECT DISTINCT
                p.id,
                p.name,
                p.description,
                p.status,
                p.start_date,
                p.deadline,
                p.project_created,
                p.project_cost,
                p.project_rate_per_hour,
                p.estimated_hours,
                COUNT(DISTINCT t.id) as total_tasks,
                COUNT(DISTINCT CASE WHEN t.status = 5 THEN t.id END) as completed_tasks,
                COUNT(DISTINCT CASE WHEN t.status IN (1,2,3,4) THEN t.id END) as active_tasks
            FROM tblprojects p
            LEFT JOIN tblclients c ON p.clientid = c.userid
            LEFT JOIN tbltasks t ON p.id = t.rel_id AND t.rel_type = 'project'
            WHERE 1=1
            """
            
            # Dynamic WHERE conditions
            conditions = []
            params = []
            
            # Text search across multiple fields
            if search_params.get('query'):
                query = f"%{search_params['query']}%"
                conditions.append("""
                    (p.name LIKE ? OR 
                     p.description LIKE ? OR
                     EXISTS (SELECT 1 FROM tbltasks t2 WHERE t2.rel_id = p.id AND t2.rel_type = 'project' AND t2.name LIKE ?))
                """)
                params.extend([query, query, query])
            
            # Status filter
            if search_params.get('status'):
                if isinstance(search_params['status'], list):
                    placeholders = ','.join(['?'] * len(search_params['status']))
                    conditions.append(f"p.status IN ({placeholders})")
                    params.extend(search_params['status'])
                else:
                    conditions.append("p.status = ?")
                    params.append(search_params['status'])
            
            # Date range filters
            if search_params.get('start_date_from'):
                conditions.append("p.start_date >= ?")
                params.append(search_params['start_date_from'])
                
            if search_params.get('start_date_to'):
                conditions.append("p.start_date <= ?")
                params.append(search_params['start_date_to'])
                
            if search_params.get('deadline_from'):
                conditions.append("p.deadline >= ?")
                params.append(search_params['deadline_from'])
                
            if search_params.get('deadline_to'):
                conditions.append("p.deadline <= ?")
                params.append(search_params['deadline_to'])
            
            # Budget range
            if search_params.get('budget_min'):
                conditions.append("p.project_cost >= ?")
                params.append(search_params['budget_min'])
                
            if search_params.get('budget_max'):
                conditions.append("p.project_cost <= ?")
                params.append(search_params['budget_max'])
            
            # Client filter
            if search_params.get('client_id'):
                conditions.append("p.clientid = ?")
                params.append(search_params['client_id'])
            
            # Overdue projects
            if search_params.get('overdue_only'):
                conditions.append("p.deadline < CURDATE() AND p.status NOT IN (4, 5)")
            
            # Active projects only
            if search_params.get('active_only'):
                conditions.append("p.status IN (1, 2, 3)")
            
            # Projects with tasks
            if search_params.get('has_tasks'):
                conditions.append("EXISTS (SELECT 1 FROM tbltasks t3 WHERE t3.rel_id = p.id AND t3.rel_type = 'project')")
            
            # Construct final query
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += """
            GROUP BY p.id, p.name, p.description, p.status, p.start_date, p.deadline, p.project_created,
                     p.project_cost, p.project_rate_per_hour, p.estimated_hours
            """
            
            # Sorting
            sort_by = search_params.get('sort_by', 'id')
            sort_order = search_params.get('sort_order', 'DESC')
            
            valid_sort_fields = ['name', 'status', 'start_date', 'deadline', 'id', 'project_cost', 'total_tasks']
            if sort_by in valid_sort_fields:
                base_query += f" ORDER BY {sort_by} {sort_order}"
            else:
                base_query += " ORDER BY p.id DESC"
            
            # Pagination
            limit = min(int(search_params.get('limit', 50)), 1000)  # Max 1000 results to accommodate all projects
            offset = int(search_params.get('offset', 0))
            base_query += f" LIMIT {limit} OFFSET {offset}"
            
            print(f"Executing search query: {base_query}")
            print(f"With parameters: {params}")
            
            cursor.execute(base_query, params)
            raw_projects = cursor.fetchall()
            
            # Process results
            projects = []
            status_map = {
                1: 'Not Started',
                2: 'In Progress', 
                3: 'On Hold',
                4: 'Cancelled',
                5: 'Finished'
            }
            
            for raw_project in raw_projects:
                project = {
                    'id': raw_project['id'],
                    'name': raw_project['name'],
                    'description': raw_project.get('description', ''),
                    'status': status_map.get(raw_project['status'], 'Unknown'),
                    'status_id': raw_project['status'],
                    'total_tasks': raw_project['total_tasks'] or 0,
                    'completed_tasks': raw_project['completed_tasks'] or 0,
                    'active_tasks': raw_project['active_tasks'] or 0,
                    'project_cost': float(raw_project.get('project_cost', 0) or 0),
                    'hourly_rate': float(raw_project.get('project_rate_per_hour', 0) or 0),
                    'estimated_hours': raw_project.get('estimated_hours', 0) or 0
                }
                
                # Handle dates
                if raw_project.get('start_date'):
                    project['start_date'] = raw_project['start_date'].strftime('%Y-%m-%d') if hasattr(raw_project['start_date'], 'strftime') else str(raw_project['start_date'])
                else:
                    project['start_date'] = None
                    
                if raw_project.get('deadline'):
                    project['deadline'] = raw_project['deadline'].strftime('%Y-%m-%d') if hasattr(raw_project['deadline'], 'strftime') else str(raw_project['deadline'])
                else:
                    project['deadline'] = None
                    
                project['created_at'] = None  # Simplified since dateadded column name is unclear
                
                # Calculate metrics
                if project['total_tasks'] > 0:
                    project['completion_percentage'] = round((project['completed_tasks'] / project['total_tasks']) * 100, 1)
                else:
                    project['completion_percentage'] = 0
                
                # Check if overdue
                if project['deadline']:
                    try:
                        deadline_date = datetime.strptime(project['deadline'], '%Y-%m-%d').date()
                        today = datetime.now().date()
                        project['is_overdue'] = deadline_date < today and project['status_id'] not in [4, 5]
                        project['days_until_deadline'] = (deadline_date - today).days
                    except:
                        project['is_overdue'] = False
                        project['days_until_deadline'] = None
                else:
                    project['is_overdue'] = False
                    project['days_until_deadline'] = None
                
                # Set priority
                if project['is_overdue']:
                    project['priority'] = 'High'
                elif project['days_until_deadline'] and project['days_until_deadline'] <= 7:
                    project['priority'] = 'Medium'
                else:
                    project['priority'] = 'Low'
                
                projects.append(project)
            
            # Get total count for pagination
            count_query = """
            SELECT COUNT(DISTINCT p.id) as total
            FROM tblprojects p
            LEFT JOIN tbltasks t ON p.id = t.rel_id AND t.rel_type = 'project'
            WHERE 1=1
            """
            
            if conditions:
                count_query += " AND " + " AND ".join(conditions)
            
            cursor.execute(count_query, params)  # Remove LIMIT params
            total_count = cursor.fetchone()['total']
            
            return jsonify({
                'success': True,
                'projects': projects,
                'total_count': total_count,
                'returned_count': len(projects),
                'search_params': search_params,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + len(projects)) < total_count
                }
            }), 200
            
        except Exception as e:
            print(f"Error searching projects: {e}")
            return jsonify({'error': f'Failed to search projects: {str(e)}'}), 500
        finally:
            if connection:
                connection.close()

# Global instance
project_controller = ProjectController()