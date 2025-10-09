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