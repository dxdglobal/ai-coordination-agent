"""
Task Management API Routes

REST API endpoints for task operations including:
- Employee task analysis
- Task status management
- Task querying and filtering
- Performance analytics
"""

from flask import Blueprint, request, jsonify
from tasks.services.employee_task_analyzer import employee_task_analyzer
from tasks.services.task_service import task_service

# Create blueprint
task_bp = Blueprint('tasks', __name__)


@task_bp.route('/employee/<employee_name>/analysis', methods=['GET'])
def get_employee_task_analysis(employee_name):
    """Get comprehensive task analysis for an employee"""
    try:
        analysis = employee_task_analyzer.generate_detailed_analysis(employee_name)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500


@task_bp.route('/employee/<employee_name>/tasks', methods=['GET'])
def get_employee_tasks(employee_name):
    """Get all tasks for a specific employee"""
    try:
        task_data = employee_task_analyzer.get_employee_tasks(employee_name)
        return jsonify(task_data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get tasks: {str(e)}'
        }), 500


@task_bp.route('/employee/<employee_name>/current', methods=['GET'])
def get_employee_current_tasks(employee_name):
    """Get current in-progress tasks for an employee"""
    try:
        task_data = employee_task_analyzer.get_employee_tasks(employee_name)
        
        if not task_data.get('success'):
            return jsonify(task_data)
        
        # Filter for current active tasks (not completed)
        active_statuses = ['in_progress', 'awaiting_feedback', 'not_started', 'testing', 'review']
        current_tasks = [
            task for task in task_data.get('tasks', [])
            if task.get('status') in active_statuses
        ]
        
        return jsonify({
            'success': True,
            'employee': task_data['employee_name'],
            'tasks': current_tasks,  # Frontend expects 'tasks' key
            'current_tasks': current_tasks,
            'total_current': len(current_tasks),
            'summary': {
                'total_tasks': task_data['total_tasks'],
                'in_progress': task_data['in_progress_tasks'],
                'completion_rate': task_data['completion_rate']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get current tasks: {str(e)}'
        }), 500


@task_bp.route('/employee/<employee_name>/overdue', methods=['GET'])
def get_employee_overdue_tasks(employee_name):
    """Get overdue tasks for a specific employee"""
    try:
        from datetime import datetime, date
        
        # Get raw task data (returns date objects)
        task_data = employee_task_analyzer.get_employee_tasks(employee_name)
        
        if not task_data.get('success'):
            return jsonify(task_data)
        
        # Filter for overdue tasks
        overdue_tasks = []
        today = datetime.now().date()
        
        for task in task_data.get('tasks', []):
            # Skip completed tasks
            if task.get('status') == 'done':
                continue
                
            due_date_obj = task.get('due_date')
            if not due_date_obj:
                continue
                
            try:
                # Handle date objects directly
                if isinstance(due_date_obj, date):
                    due_date = due_date_obj
                elif isinstance(due_date_obj, str):
                    if due_date_obj == 'None':
                        continue
                    # Parse string format if needed
                    if ',' in due_date_obj:
                        date_part = due_date_obj.split(',')[1].strip()
                        date_str = date_part[:11]
                        due_date = datetime.strptime(date_str, '%d %b %Y').date()
                    else:
                        continue
                else:
                    continue
                    
                # Check if overdue
                if due_date < today:
                    # Calculate days overdue
                    days_overdue = (today - due_date).days
                    
                    # Create task copy with serialized dates for JSON
                    task_copy = {}
                    for key, value in task.items():
                        if isinstance(value, datetime):
                            task_copy[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(value, date):
                            task_copy[key] = value.strftime('%Y-%m-%d')
                        else:
                            task_copy[key] = value
                    
                    task_copy['days_overdue'] = days_overdue
                    overdue_tasks.append(task_copy)
                        
            except Exception as e:
                # Skip tasks with invalid date formats
                continue
        
        # Sort by days overdue (most overdue first)
        overdue_tasks.sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'employee': task_data.get('employee_name', employee_name),
            'tasks': overdue_tasks,  # Frontend expects 'tasks' key
            'overdue_tasks': overdue_tasks,
            'total_overdue': len(overdue_tasks),
            'summary': {
                'total_tasks': task_data.get('total_tasks', len(task_data.get('tasks', []))),
                'overdue_tasks': len(overdue_tasks),
                'completion_rate': task_data.get('completion_rate', 0),
                'most_overdue_days': overdue_tasks[0].get('days_overdue', 0) if overdue_tasks else 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get overdue tasks: {str(e)}'
        }), 500


@task_bp.route('/status/<status>', methods=['GET'])
def get_tasks_by_status(status):
    """Get all tasks with a specific status"""
    try:
        result = task_service.get_tasks_by_status(status)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get tasks by status: {str(e)}'
        }), 500


@task_bp.route('/overdue', methods=['GET'])
def get_overdue_tasks():
    """Get all overdue tasks"""
    try:
        result = task_service.get_overdue_tasks()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get overdue tasks: {str(e)}'
        }), 500


@task_bp.route('/<int:task_id>', methods=['GET'])
def get_task_details(task_id):
    """Get detailed information about a specific task"""
    try:
        result = task_service.get_task_by_id(task_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get task details: {str(e)}'
        }), 500


@task_bp.route('/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Update task status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        result = task_service.update_task_status(task_id, new_status)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update task status: {str(e)}'
        }), 500


@task_bp.route('/analytics/summary', methods=['GET'])
def get_task_analytics_summary():
    """Get overall task analytics summary"""
    try:
        # Get tasks by different statuses
        in_progress = task_service.get_tasks_by_status('in_progress')
        completed = task_service.get_tasks_by_status('done')
        overdue = task_service.get_overdue_tasks()
        not_started = task_service.get_tasks_by_status('not_started')
        
        summary = {
            'success': True,
            'summary': {
                'in_progress': in_progress.get('total', 0) if in_progress.get('success') else 0,
                'completed': completed.get('total', 0) if completed.get('success') else 0,
                'overdue': overdue.get('total', 0) if overdue.get('success') else 0,
                'not_started': not_started.get('total', 0) if not_started.get('success') else 0,
            },
            'overdue_tasks': overdue.get('tasks', [])[:5] if overdue.get('success') else []  # Top 5 overdue
        }
        
        total_active = (summary['summary']['in_progress'] + 
                       summary['summary']['completed'] + 
                       summary['summary']['not_started'])
        
        if total_active > 0:
            summary['summary']['completion_rate'] = (
                summary['summary']['completed'] / total_active * 100
            )
        else:
            summary['summary']['completion_rate'] = 0
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get analytics summary: {str(e)}'
        }), 500


# Health check for tasks module
@task_bp.route('/health', methods=['GET'])
def tasks_health_check():
    """Health check endpoint for tasks module"""
    return jsonify({
        'status': 'healthy',
        'module': 'tasks',
        'version': '1.0.0',
        'features': [
            'Employee task analysis',
            'Task status management',
            'Performance analytics',
            'Overdue task tracking'
        ]
    })