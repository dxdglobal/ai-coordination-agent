from flask import Blueprint, request, jsonify
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

# Import here to avoid circular imports
from models.models import db, Task, Project, Comment, AIAction, TaskStatus, Priority
from services.ai_service import AICoordinationService
from services.deepseek_service import DeepseekService

ai_service = AICoordinationService()
deepseek_service = DeepseekService()

@ai_bp.route('/database-analytics', methods=['POST'])
def database_analytics():
    """
    Answer database analytics questions using AI
    Examples: "How many tables?", "Total projects?", "Show me stats"
    """
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        result = deepseek_service.database_analytics(query)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/search', methods=['POST'])
def intelligent_search():
    """
    Intelligent search using Deepseek AI across all project data
    """
    data = request.get_json()
    query = data.get('query', '')
    limit = data.get('limit', 20)
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    try:
        results = deepseek_service.intelligent_search(query, limit)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/search/chat', methods=['POST'])
def search_chat():
    """
    Follow-up questions about search results
    """
    data = request.get_json()
    query = data.get('query', '')
    results = data.get('results', [])
    follow_up = data.get('follow_up', '')
    
    if not query or not follow_up:
        return jsonify({'error': 'Query and follow-up question are required'}), 400
    
    try:
        response = deepseek_service.chat_about_results(query, results, follow_up)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/analyze', methods=['POST'])
def analyze_tasks():
    """
    Analyze tasks and projects based on AI prompt and suggest actions
    """
    data = request.get_json()
    prompt = data.get('prompt', 'You are a coordination agent, follow up all tasks and projects')
    
    try:
        analysis = ai_service.analyze_workspace(prompt)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/chat', methods=['POST'])
def chat_with_ai():
    """
    Chat interface for AI agent
    """
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        response = ai_service.chat(message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """
    Get AI suggestions for improving project coordination
    """
    try:
        suggestions = ai_service.get_coordination_suggestions()
        return jsonify(suggestions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/actions', methods=['GET'])
def get_pending_actions():
    """
    Get pending AI actions that need to be executed
    """
    actions = AIAction.query.filter_by(executed=False).order_by(AIAction.created_at.desc()).all()
    return jsonify([action.to_dict() for action in actions])

@ai_bp.route('/actions/<int:action_id>/execute', methods=['POST'])
def execute_action(action_id):
    """
    Execute a pending AI action
    """
    action = AIAction.query.get_or_404(action_id)
    
    try:
        result = ai_service.execute_action(action)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/auto-assign', methods=['POST'])
def auto_assign_tasks():
    """
    Auto-assign tasks based on AI analysis
    """
    data = request.get_json()
    project_id = data.get('project_id')
    
    try:
        result = ai_service.auto_assign_tasks(project_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/priority-analysis', methods=['POST'])
def analyze_priorities():
    """
    Analyze and suggest task priority changes
    """
    data = request.get_json()
    project_id = data.get('project_id')
    
    try:
        analysis = ai_service.analyze_task_priorities(project_id)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/time-analysis', methods=['GET'])
def analyze_time_tracking():
    """
    Analyze time tracking data and provide insights
    """
    try:
        analysis = ai_service.analyze_time_tracking()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500