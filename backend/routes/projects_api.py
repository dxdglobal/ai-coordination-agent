"""
Projects Routes
API endpoints for project management using CRM database
"""

from flask import Blueprint, request, jsonify
from controllers.project_controller import project_controller

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """Get all projects - publicly accessible"""
    try:
        return project_controller.get_all_projects()
    except Exception as e:
        return jsonify({'error': f'Failed to fetch projects: {str(e)}'}), 500

@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project by ID"""
    try:
        return project_controller.get_project_by_id(project_id)
    except Exception as e:
        return jsonify({'error': f'Failed to fetch project: {str(e)}'}), 500

@projects_bp.route('/stats', methods=['GET'])
def get_projects_stats():
    """Get projects statistics dashboard"""
    try:
        # Get all projects first
        response = project_controller.get_all_projects()
        
        if response[1] != 200:  # Check status code
            return response
        
        projects_data = response[0].get_json()
        projects = projects_data.get('projects', [])
        
        # Calculate statistics
        stats = {
            'total_projects': len(projects),
            'active_projects': len([p for p in projects if p['status_id'] == 2]),
            'completed_projects': len([p for p in projects if p['status_id'] == 5]),
            'overdue_projects': len([p for p in projects if p.get('is_overdue', False)]),
            'total_tasks': sum(p['total_tasks'] for p in projects),
            'completed_tasks': sum(p['completed_tasks'] for p in projects),
            'average_completion': round(sum(p['completion_percentage'] for p in projects) / len(projects), 1) if projects else 0,
            'projects_by_status': {},
            'projects_by_priority': {'High': 0, 'Medium': 0, 'Low': 0}
        }
        
        # Group by status
        for project in projects:
            status = project['status']
            stats['projects_by_status'][status] = stats['projects_by_status'].get(status, 0) + 1
            
            # Count by priority
            priority = project.get('priority', 'Low')
            stats['projects_by_priority'][priority] += 1
        
        return jsonify({
            'success': True,
            'stats': stats,
            'recent_projects': projects[:5]  # Return 5 most recent projects
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch project statistics: {str(e)}'}), 500

@projects_bp.route('/search', methods=['GET', 'POST'])
def search_projects():
    """
    Advanced project search with multiple filters
    
    GET: Search using query parameters
    POST: Search using JSON body for complex filters
    
    Search parameters:
    - query: Text search across name, description, client name, tasks
    - status: Project status (1-5) or list of statuses
    - start_date_from/to: Date range for project start
    - deadline_from/to: Date range for project deadline
    - budget_min/max: Budget range filter
    - client_id: Filter by specific client
    - overdue_only: Boolean - only overdue projects
    - active_only: Boolean - only active projects (status 1,2,3)
    - has_tasks: Boolean - only projects with tasks
    - sort_by: Field to sort by (name, status, start_date, deadline, dateadded, project_cost, total_tasks)
    - sort_order: ASC or DESC
    - limit: Max results (default 50, max 100)
    - offset: Pagination offset
    """
    try:
        # Get search parameters from either query params or JSON body
        if request.method == 'POST':
            search_params = request.get_json() or {}
        else:
            search_params = request.args.to_dict()
            
        # Convert string parameters to appropriate types
        if 'status' in search_params:
            if isinstance(search_params['status'], str):
                # Handle comma-separated status values
                if ',' in search_params['status']:
                    search_params['status'] = [int(s.strip()) for s in search_params['status'].split(',')]
                else:
                    search_params['status'] = int(search_params['status'])
        
        # Convert boolean parameters
        for bool_param in ['overdue_only', 'active_only', 'has_tasks']:
            if bool_param in search_params:
                search_params[bool_param] = str(search_params[bool_param]).lower() in ['true', '1', 'yes']
        
        # Convert numeric parameters
        for num_param in ['budget_min', 'budget_max', 'client_id', 'limit', 'offset']:
            if num_param in search_params and search_params[num_param]:
                try:
                    search_params[num_param] = int(search_params[num_param])
                except ValueError:
                    pass
        
        return project_controller.search_projects(search_params)
        
    except Exception as e:
        return jsonify({'error': f'Failed to search projects: {str(e)}'}), 500

@projects_bp.route('/search/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get search suggestions for autocomplete"""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({'suggestions': []}), 200
            
        # This would typically use a more sophisticated search index
        # For now, we'll do a simple database query
        return jsonify({
            'suggestions': [
                f"Projects containing '{query}'",
                f"Active projects with '{query}'",
                f"Completed projects with '{query}'",
                f"Client projects with '{query}'"
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get suggestions: {str(e)}'}), 500