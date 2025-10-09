"""
CRM Tasks API routes
Handles task operations from CRM database
"""

from flask import Blueprint, jsonify, request
from controllers.task_controller import TaskController

crm_tasks_api = Blueprint('crm_tasks_api', __name__)

@crm_tasks_api.route('/crm/tasks/search', methods=['GET'])
def search_crm_tasks():
    """Search tasks from CRM database with filters"""
    try:
        task_controller = TaskController()
        
        # Get filters from query parameters
        filters = {}
        
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('priority'):
            filters['priority'] = request.args.get('priority')
        
        if request.args.get('title'):
            filters['title'] = request.args.get('title')
        
        if request.args.get('assignee'):
            filters['assignee'] = request.args.get('assignee')
        
        if request.args.get('project_id'):
            filters['project_id'] = request.args.get('project_id')
        
        # Add pagination and sorting
        if request.args.get('limit'):
            filters['limit'] = int(request.args.get('limit'))
        
        if request.args.get('offset'):
            filters['offset'] = int(request.args.get('offset'))
        
        if request.args.get('sort_by'):
            filters['sort_by'] = request.args.get('sort_by')
        
        if request.args.get('sort_order'):
            filters['sort_order'] = request.args.get('sort_order')
        
        # Search tasks
        response, status_code = task_controller.search_tasks(filters)
        return response, status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'tasks': [],
            'total': 0
        }), 500

@crm_tasks_api.route('/crm/tasks', methods=['GET'])
def get_all_crm_tasks():
    """Get all tasks from CRM database"""
    try:
        task_controller = TaskController()
        response, status_code = task_controller.get_all_tasks()
        return response, status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'tasks': [],
            'total_count': 0
        }), 500

@crm_tasks_api.route('/crm/tasks/stats', methods=['GET'])
def get_crm_task_stats():
    """Get task statistics from CRM database"""
    try:
        task_controller = TaskController()
        response, status_code = task_controller.get_task_stats()
        return response, status_code
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "stats": {}
        }), 500

@crm_tasks_api.route('/crm/tasks/<int:task_id>', methods=['GET'])
def get_crm_task_by_id(task_id):
    """Get a specific task by ID from CRM database"""
    try:
        task_controller = TaskController()
        response, status_code = task_controller.get_task_by_id(task_id)
        return response, status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'task': None
        }), 500