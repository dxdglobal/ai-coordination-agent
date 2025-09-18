from flask import Blueprint, request, jsonify
from app import db
from models import Task, Project, Comment, AIAction, TaskStatus, Priority
from services.ai_service import AICoordinationService
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

ai_service = AICoordinationService()

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