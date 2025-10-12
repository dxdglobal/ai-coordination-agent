#!/usr/bin/env python3
"""
Employee Overdue Tasks API
=========================

API endpoints for retrieving overdue tasks for specific employees
using direct CRM database queries for accurate results.
"""

from flask import Blueprint, jsonify, request
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

employee_overdue_api = Blueprint('employee_overdue_api', __name__)

def get_database_connection():
    """Get direct MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', '92.113.22.65'),
            database=os.getenv('DB_NAME', 'u906714182_sqlrrefdvdv'),
            user=os.getenv('DB_USER', 'u906714182_sqlrrefdvdv'),
            password=os.getenv('DB_PASSWORD', '3@6*t:lU'),
            port=int(os.getenv('DB_PORT', '3306'))
        )
        return connection
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def find_employee_id(employee_name):
    """Find employee ID from staff table"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Search for employee in staff table
        search_query = """
        SELECT staffid, firstname, lastname, CONCAT(firstname, ' ', lastname) as full_name
        FROM tblstaff 
        WHERE LOWER(firstname) LIKE %s 
           OR LOWER(lastname) LIKE %s
           OR LOWER(CONCAT(firstname, ' ', lastname)) LIKE %s
        """
        
        search_term = f"%{employee_name.lower()}%"
        cursor.execute(search_query, (search_term, search_term, search_term))
        results = cursor.fetchall()
        
        if results:
            return results[0]['staffid'], results[0]['full_name']
        return None, None
        
    except Exception as e:
        print(f"❌ Error finding employee: {e}")
        return None, None
    finally:
        connection.close()

@employee_overdue_api.route('/api/employee/<employee_name>/overdue-tasks', methods=['GET'])
def get_employee_overdue_tasks(employee_name):
    """Get overdue tasks for a specific employee"""
    
    # Find employee ID
    employee_id, full_name = find_employee_id(employee_name)
    if not employee_id:
        return jsonify({
            'success': False,
            'error': f'Employee "{employee_name}" not found',
            'overdue_tasks': [],
            'stats': {}
        }), 404
    
    connection = get_database_connection()
    if not connection:
        return jsonify({
            'success': False,
            'error': 'Database connection failed',
            'overdue_tasks': [],
            'stats': {}
        }), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all tasks assigned to the employee with detailed information
        task_query = """
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
            t.rel_id,
            t.rel_type,
            p.name as project_name,
            p.clientid,
            c.company as client_name,
            s.firstname,
            s.lastname,
            ta.staffid as assigned_staff_id,
            CASE 
                WHEN t.status = 1 THEN 'Not Started'
                WHEN t.status = 2 THEN 'In Progress' 
                WHEN t.status = 3 THEN 'Testing'
                WHEN t.status = 4 THEN 'Awaiting Feedback'
                WHEN t.status = 5 THEN 'Complete'
                ELSE CONCAT('Status ', t.status)
            END as status_name,
            CASE 
                WHEN t.priority = 1 THEN 'Low'
                WHEN t.priority = 2 THEN 'Medium'
                WHEN t.priority = 3 THEN 'High'
                WHEN t.priority = 4 THEN 'Urgent'
                ELSE CONCAT('Priority ', t.priority)
            END as priority_name,
            DATEDIFF(CURDATE(), t.duedate) as days_overdue
        FROM tbltasks t
        INNER JOIN tbltask_assigned ta ON t.id = ta.taskid
        LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
        LEFT JOIN tblclients c ON p.clientid = c.userid
        LEFT JOIN tblstaff s ON ta.staffid = s.staffid
        WHERE ta.staffid = %s
        ORDER BY t.duedate ASC
        """
        
        cursor.execute(task_query, (employee_id,))
        all_tasks = cursor.fetchall()
        
        if not all_tasks:
            return jsonify({
                'success': True,
                'employee_name': full_name,
                'employee_id': employee_id,
                'overdue_tasks': [],
                'stats': {
                    'total_tasks': 0,
                    'overdue_count': 0,
                    'completed_count': 0,
                    'upcoming_count': 0
                }
            })
        
        # Filter overdue tasks
        overdue_tasks = []
        upcoming_tasks = []
        completed_tasks = []
        
        for task in all_tasks:
            # Check if task is completed
            if task['status'] == 5:  # Status 5 = Complete
                completed_tasks.append(task)
                continue
            
            # Check if task has due date
            if not task['duedate']:
                continue
            
            try:
                due_date = task['duedate']
                
                # Handle different date formats
                if isinstance(due_date, str):
                    due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                elif hasattr(due_date, 'date'):
                    due_date = due_date.date() if callable(due_date.date) else due_date
                elif not hasattr(due_date, 'year'):
                    continue
                
                current_date = datetime.now().date()
                
                # Task is overdue if due date is in the past and not completed
                if due_date < current_date and task['status'] != 5:
                    days_overdue = (current_date - due_date).days
                    task['days_overdue'] = days_overdue
                    task['duedate'] = due_date.strftime('%Y-%m-%d')
                    overdue_tasks.append(task)
                elif due_date >= current_date:
                    days_until_due = (due_date - current_date).days
                    task['days_until_due'] = days_until_due
                    task['duedate'] = due_date.strftime('%Y-%m-%d')
                    upcoming_tasks.append(task)
                    
            except Exception as e:
                print(f"⚠️ Error processing date for task {task['task_id']}: {e}")
                continue
        
        # Sort overdue tasks by days overdue (most overdue first)
        overdue_tasks.sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
        
        # Priority breakdown
        priority_breakdown = {}
        for task in overdue_tasks:
            priority = task['priority_name']
            if priority not in priority_breakdown:
                priority_breakdown[priority] = []
            priority_breakdown[priority].append({
                'task_id': task['task_id'],
                'task_name': task['task_name'],
                'days_overdue': task['days_overdue'],
                'project_name': task['project_name']
            })
        
        # Project breakdown
        project_breakdown = {}
        for task in overdue_tasks:
            project = task['project_name'] or 'No Project'
            if project not in project_breakdown:
                project_breakdown[project] = 0
            project_breakdown[project] += 1
        
        # Urgency analysis
        critical_tasks = [t for t in overdue_tasks if t['days_overdue'] > 30]
        urgent_tasks = [t for t in overdue_tasks if 7 < t['days_overdue'] <= 30]
        recent_tasks = [t for t in overdue_tasks if t['days_overdue'] <= 7]
        
        return jsonify({
            'success': True,
            'employee_name': full_name,
            'employee_id': employee_id,
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overdue_tasks': overdue_tasks,
            'upcoming_tasks': upcoming_tasks[:5],  # Limit to 5 upcoming
            'stats': {
                'total_tasks': len(all_tasks),
                'overdue_count': len(overdue_tasks),
                'completed_count': len(completed_tasks),
                'upcoming_count': len(upcoming_tasks)
            },
            'analysis': {
                'priority_breakdown': priority_breakdown,
                'project_breakdown': project_breakdown,
                'urgency_analysis': {
                    'critical_count': len(critical_tasks),
                    'urgent_count': len(urgent_tasks),
                    'recent_count': len(recent_tasks)
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database query failed: {str(e)}',
            'overdue_tasks': [],
            'stats': {}
        }), 500
    finally:
        connection.close()

@employee_overdue_api.route('/api/employee/<employee_name>/completed-tasks', methods=['GET'])
def get_employee_completed_tasks(employee_name):
    """Get completed tasks for a specific employee"""
    
    # Find employee ID
    employee_id, full_name = find_employee_id(employee_name)
    if not employee_id:
        return jsonify({
            'success': False,
            'error': f'Employee "{employee_name}" not found',
            'completed_tasks': [],
            'stats': {}
        }), 404
    
    connection = get_database_connection()
    if not connection:
        return jsonify({
            'success': False,
            'error': 'Database connection failed',
            'completed_tasks': [],
            'stats': {}
        }), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get completed tasks assigned to the employee
        task_query = """
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
            t.rel_id,
            t.rel_type,
            p.name as project_name,
            p.clientid,
            c.company as client_name,
            s.firstname,
            s.lastname,
            ta.staffid as assigned_staff_id,
            CASE 
                WHEN t.status = 1 THEN 'Not Started'
                WHEN t.status = 2 THEN 'In Progress' 
                WHEN t.status = 3 THEN 'Testing'
                WHEN t.status = 4 THEN 'Awaiting Feedback'
                WHEN t.status = 5 THEN 'Complete'
                ELSE CONCAT('Status ', t.status)
            END as status_name,
            CASE 
                WHEN t.priority = 1 THEN 'Low'
                WHEN t.priority = 2 THEN 'Medium'
                WHEN t.priority = 3 THEN 'High'
                WHEN t.priority = 4 THEN 'Urgent'
                ELSE CONCAT('Priority ', t.priority)
            END as priority_name,
            DATEDIFF(t.datefinished, t.startdate) as completion_days
        FROM tbltasks t
        INNER JOIN tbltask_assigned ta ON t.id = ta.taskid
        LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
        LEFT JOIN tblclients c ON p.clientid = c.userid
        LEFT JOIN tblstaff s ON ta.staffid = s.staffid
        WHERE ta.staffid = %s AND t.status = 5
        ORDER BY t.datefinished DESC
        """
        
        cursor.execute(task_query, (employee_id,))
        completed_tasks = cursor.fetchall()
        
        # Get all tasks for stats
        stats_query = """
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN t.status = 5 THEN 1 ELSE 0 END) as completed_count
        FROM tbltasks t
        INNER JOIN tbltask_assigned ta ON t.id = ta.taskid
        WHERE ta.staffid = %s
        """
        
        cursor.execute(stats_query, (employee_id,))
        stats_result = cursor.fetchone()
        
        # Format completed tasks
        for task in completed_tasks:
            if task['datefinished']:
                task['datefinished'] = task['datefinished'].strftime('%Y-%m-%d') if hasattr(task['datefinished'], 'strftime') else str(task['datefinished'])
            if task['duedate']:
                task['duedate'] = task['duedate'].strftime('%Y-%m-%d') if hasattr(task['duedate'], 'strftime') else str(task['duedate'])
            if task['startdate']:
                task['startdate'] = task['startdate'].strftime('%Y-%m-%d') if hasattr(task['startdate'], 'strftime') else str(task['startdate'])
        
        # Priority breakdown
        priority_breakdown = {}
        for task in completed_tasks:
            priority = task['priority_name']
            if priority not in priority_breakdown:
                priority_breakdown[priority] = []
            priority_breakdown[priority].append({
                'task_id': task['task_id'],
                'task_name': task['task_name'],
                'completion_days': task['completion_days'],
                'project_name': task['project_name']
            })
        
        # Project breakdown
        project_breakdown = {}
        for task in completed_tasks:
            project = task['project_name'] or 'No Project'
            if project not in project_breakdown:
                project_breakdown[project] = 0
            project_breakdown[project] += 1
        
        return jsonify({
            'success': True,
            'employee_name': full_name,
            'employee_id': employee_id,
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'completed_tasks': completed_tasks,
            'stats': {
                'total_tasks': stats_result['total_tasks'] or 0,
                'completed_count': len(completed_tasks),
                'completion_rate': round((len(completed_tasks) / max(stats_result['total_tasks'], 1)) * 100, 1)
            },
            'analysis': {
                'priority_breakdown': priority_breakdown,
                'project_breakdown': project_breakdown
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database query failed: {str(e)}',
            'completed_tasks': [],
            'stats': {}
        }), 500
    finally:
        connection.close()

@employee_overdue_api.route('/api/employee/<employee_name>/inprogress-tasks', methods=['GET'])
def get_employee_inprogress_tasks(employee_name):
    """Get in-progress tasks for a specific employee"""
    
    # Find employee ID
    employee_id, full_name = find_employee_id(employee_name)
    if not employee_id:
        return jsonify({
            'success': False,
            'error': f'Employee "{employee_name}" not found',
            'inprogress_tasks': [],
            'stats': {}
        }), 404
    
    connection = get_database_connection()
    if not connection:
        return jsonify({
            'success': False,
            'error': 'Database connection failed',
            'inprogress_tasks': [],
            'stats': {}
        }), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get in-progress tasks assigned to the employee (status 2, 3, 4)
        task_query = """
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
            t.rel_id,
            t.rel_type,
            p.name as project_name,
            p.clientid,
            c.company as client_name,
            s.firstname,
            s.lastname,
            ta.staffid as assigned_staff_id,
            CASE 
                WHEN t.status = 1 THEN 'Not Started'
                WHEN t.status = 2 THEN 'In Progress' 
                WHEN t.status = 3 THEN 'Testing'
                WHEN t.status = 4 THEN 'Awaiting Feedback'
                WHEN t.status = 5 THEN 'Complete'
                ELSE CONCAT('Status ', t.status)
            END as status_name,
            CASE 
                WHEN t.priority = 1 THEN 'Low'
                WHEN t.priority = 2 THEN 'Medium'
                WHEN t.priority = 3 THEN 'High'
                WHEN t.priority = 4 THEN 'Urgent'
                ELSE CONCAT('Priority ', t.priority)
            END as priority_name,
            CASE 
                WHEN t.duedate IS NOT NULL THEN DATEDIFF(t.duedate, CURDATE())
                ELSE NULL
            END as days_until_due
        FROM tbltasks t
        INNER JOIN tbltask_assigned ta ON t.id = ta.taskid
        LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
        LEFT JOIN tblclients c ON p.clientid = c.userid
        LEFT JOIN tblstaff s ON ta.staffid = s.staffid
        WHERE ta.staffid = %s AND t.status IN (2, 3, 4)
        ORDER BY t.priority DESC, t.duedate ASC
        """
        
        cursor.execute(task_query, (employee_id,))
        inprogress_tasks = cursor.fetchall()
        
        # Get all tasks for stats
        stats_query = """
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN t.status IN (2, 3, 4) THEN 1 ELSE 0 END) as inprogress_count
        FROM tbltasks t
        INNER JOIN tbltask_assigned ta ON t.id = ta.taskid
        WHERE ta.staffid = %s
        """
        
        cursor.execute(stats_query, (employee_id,))
        stats_result = cursor.fetchone()
        
        # Format in-progress tasks
        for task in inprogress_tasks:
            if task['duedate']:
                task['duedate'] = task['duedate'].strftime('%Y-%m-%d') if hasattr(task['duedate'], 'strftime') else str(task['duedate'])
            if task['startdate']:
                task['startdate'] = task['startdate'].strftime('%Y-%m-%d') if hasattr(task['startdate'], 'strftime') else str(task['startdate'])
        
        # Status breakdown
        status_breakdown = {}
        for task in inprogress_tasks:
            status = task['status_name']
            if status not in status_breakdown:
                status_breakdown[status] = []
            status_breakdown[status].append({
                'task_id': task['task_id'],
                'task_name': task['task_name'],
                'days_until_due': task['days_until_due'],
                'project_name': task['project_name']
            })
        
        # Priority breakdown
        priority_breakdown = {}
        for task in inprogress_tasks:
            priority = task['priority_name']
            if priority not in priority_breakdown:
                priority_breakdown[priority] = []
            priority_breakdown[priority].append({
                'task_id': task['task_id'],
                'task_name': task['task_name'],
                'days_until_due': task['days_until_due'],
                'project_name': task['project_name']
            })
        
        # Project breakdown
        project_breakdown = {}
        for task in inprogress_tasks:
            project = task['project_name'] or 'No Project'
            if project not in project_breakdown:
                project_breakdown[project] = 0
            project_breakdown[project] += 1
        
        return jsonify({
            'success': True,
            'employee_name': full_name,
            'employee_id': employee_id,
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'inprogress_tasks': inprogress_tasks,
            'stats': {
                'total_tasks': stats_result['total_tasks'] or 0,
                'inprogress_count': len(inprogress_tasks),
                'inprogress_rate': round((len(inprogress_tasks) / max(stats_result['total_tasks'], 1)) * 100, 1)
            },
            'analysis': {
                'status_breakdown': status_breakdown,
                'priority_breakdown': priority_breakdown,
                'project_breakdown': project_breakdown
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database query failed: {str(e)}',
            'inprogress_tasks': [],
            'stats': {}
        }), 500
    finally:
        connection.close()

@employee_overdue_api.route('/api/employee/<employee_name>/task-summary', methods=['GET'])
def get_employee_task_summary(employee_name):
    """Get quick task summary for an employee"""
    
    # Find employee ID
    employee_id, full_name = find_employee_id(employee_name)
    if not employee_id:
        return jsonify({
            'success': False,
            'error': f'Employee "{employee_name}" not found'
        }), 404
    
    connection = get_database_connection()
    if not connection:
        return jsonify({
            'success': False,
            'error': 'Database connection failed'
        }), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get task counts by status
        summary_query = """
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN t.status = 5 THEN 1 ELSE 0 END) as completed_tasks,
            SUM(CASE WHEN t.status != 5 AND t.duedate IS NOT NULL AND t.duedate < CURDATE() THEN 1 ELSE 0 END) as overdue_tasks,
            SUM(CASE WHEN t.status != 5 AND t.duedate IS NOT NULL AND t.duedate >= CURDATE() THEN 1 ELSE 0 END) as upcoming_tasks
        FROM tbltasks t
        INNER JOIN tbltask_assigned ta ON t.id = ta.taskid
        WHERE ta.staffid = %s
        """
        
        cursor.execute(summary_query, (employee_id,))
        result = cursor.fetchone()
        
        completion_rate = 0
        if result['total_tasks'] > 0:
            completion_rate = round((result['completed_tasks'] / result['total_tasks']) * 100, 1)
        
        return jsonify({
            'success': True,
            'employee_name': full_name,
            'employee_id': employee_id,
            'summary': {
                'total_tasks': result['total_tasks'] or 0,
                'completed_tasks': result['completed_tasks'] or 0,
                'overdue_tasks': result['overdue_tasks'] or 0,
                'upcoming_tasks': result['upcoming_tasks'] or 0,
                'completion_rate': completion_rate
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Summary query failed: {str(e)}'
        }), 500
    finally:
        connection.close()