from flask import Blueprint, request, jsonify, g
from datetime import datetime
import asyncio
from services.ai_task_service import ai_task_service

ai_tasks_bp = Blueprint('ai_tasks', __name__)

@ai_tasks_bp.route('/ai/tasks/query', methods=['POST'])
def process_task_query():
    """Process natural language task queries with AI"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required',
                'suggestions': ['Please provide a task-related question or request']
            }), 400
        
        # Get user context
        user_context = {}
        if hasattr(g, 'current_user') and g.current_user:
            user_context = {
                'user_id': g.current_user.get('id'),
                'username': g.current_user.get('username'),
                'role': g.current_user.get('role')
            }
        
        # Process the query asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            ai_task_service.process_task_query(query, user_context)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'suggestions': [
                'Try rephrasing your request',
                'Check your connection and try again',
                'Be more specific about what you want to do'
            ]
        }), 500

@ai_tasks_bp.route('/ai/tasks/smart-create', methods=['POST'])
def smart_create_task():
    """Create tasks using natural language description"""
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        
        if not description:
            return jsonify({
                'success': False,
                'error': 'Task description is required'
            }), 400
        
        # Use AI to parse the description and create a task
        query = f"Create a task: {description}"
        
        user_context = {}
        if hasattr(g, 'current_user') and g.current_user:
            user_context = {
                'user_id': g.current_user.get('id'),
                'username': g.current_user.get('username'),
                'role': g.current_user.get('role')
            }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            ai_task_service.process_task_query(query, user_context)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_tasks_bp.route('/ai/tasks/analyze', methods=['POST'])
def analyze_tasks():
    """Analyze tasks with AI insights"""
    try:
        data = request.get_json()
        filters = data.get('filters', {})
        
        query = "Analyze my tasks"
        if filters:
            filter_desc = []
            if filters.get('status'):
                filter_desc.append(f"status: {filters['status']}")
            if filters.get('assignee'):
                filter_desc.append(f"assigned to: {filters['assignee']}")
            if filters.get('priority'):
                filter_desc.append(f"priority: {filters['priority']}")
            
            if filter_desc:
                query += f" with {', '.join(filter_desc)}"
        
        user_context = {}
        if hasattr(g, 'current_user') and g.current_user:
            user_context = {
                'user_id': g.current_user.get('id'),
                'username': g.current_user.get('username'),
                'role': g.current_user.get('role')
            }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            ai_task_service.process_task_query(query, user_context)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_tasks_bp.route('/ai/tasks/suggestions', methods=['GET'])
def get_task_suggestions():
    """Get AI-powered task suggestions"""
    try:
        # Get common task management suggestions
        suggestions = [
            "Show me all high priority tasks",
            "List overdue tasks",
            "Create a new task for database optimization",
            "Analyze team productivity this week",
            "Find tasks assigned to John",
            "Show completed tasks from last month",
            "Update all pending tasks to in progress",
            "List all urgent tasks due this week"
        ]
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_tasks_bp.route('/ai/tasks/semantic-search', methods=['POST'])
def semantic_task_search():
    """Enhanced semantic search for tasks"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        # Use existing vector service for semantic search
        from services.vector_service import VectorDatabaseService
        vector_service = VectorDatabaseService()
        
        results = vector_service.semantic_search(query, limit)
        
        # Enhance results with AI analysis
        user_context = {}
        if hasattr(g, 'current_user') and g.current_user:
            user_context = {
                'user_id': g.current_user.get('id'),
                'username': g.current_user.get('username'),
                'role': g.current_user.get('role')
            }
        
        search_query = f"Search and analyze: {query}"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ai_result = loop.run_until_complete(
            ai_task_service.process_task_query(search_query, user_context)
        )
        loop.close()
        
        return jsonify({
            'success': True,
            'results': results.get('results', []),
            'ai_insights': ai_result.get('ai_response', ''),
            'query': query,
            'total_found': len(results.get('results', []))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'results': []
        }), 500

@ai_tasks_bp.route('/ai/tasks/quick-actions', methods=['POST'])
def quick_task_actions():
    """Quick task actions with AI assistance"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'mark_complete', 'assign', 'prioritize', etc.
        task_ids = data.get('task_ids', [])
        params = data.get('params', {})
        
        if not action or not task_ids:
            return jsonify({
                'success': False,
                'error': 'Action and task IDs are required'
            }), 400
        
        # Map quick actions to queries
        action_queries = {
            'mark_complete': 'Mark selected tasks as completed',
            'mark_progress': 'Mark selected tasks as in progress',
            'assign': f"Assign selected tasks to {params.get('assignee', 'user')}",
            'high_priority': 'Set selected tasks to high priority',
            'urgent_priority': 'Set selected tasks to urgent priority'
        }
        
        query = action_queries.get(action, f'Perform {action} on selected tasks')
        
        user_context = {}
        if hasattr(g, 'current_user') and g.current_user:
            user_context = {
                'user_id': g.current_user.get('id'),
                'username': g.current_user.get('username'),
                'role': g.current_user.get('role')
            }
        
        # Add task IDs context
        user_context['selected_task_ids'] = task_ids
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            ai_task_service.process_task_query(query, user_context)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_tasks_bp.route('/ai/tasks/health', methods=['GET'])
def task_system_health():
    """Check AI task system health"""
    try:
        from models.models import Task
        from services.vector_service import VectorDatabaseService
        
        # Basic health checks
        total_tasks = Task.query.count()
        
        vector_service = VectorDatabaseService()
        vector_stats = vector_service.get_collection_stats()
        
        return jsonify({
            'success': True,
            'health': 'healthy',
            'stats': {
                'total_tasks': total_tasks,
                'vector_embeddings': vector_stats.get('task_embeddings', 0),
                'ai_service': 'available' if ai_task_service.openai_api_key else 'limited'
            },
            'capabilities': [
                'Natural language task queries',
                'Smart task creation',
                'AI-powered task analysis',
                'Semantic task search',
                'Quick task actions',
                'Task performance insights'
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'health': 'degraded',
            'error': str(e)
        }), 500