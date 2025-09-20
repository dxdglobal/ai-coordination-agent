from flask import Blueprint, request, jsonify
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

# Import here to avoid circular imports
from models.models import db, Task, Project, Comment, AIAction, TaskStatus, Priority
from services.ai_service import AICoordinationService
from services.deepseek_service import DeepseekService
from services.ai_provider_service import AIProviderService
from services.enhanced_ai_service import EnhancedAIService
from services.rl_ai_service import ReinforcementLearningAI

ai_service = AICoordinationService()
deepseek_service = DeepseekService()
ai_provider_service = AIProviderService()
enhanced_ai_service = EnhancedAIService()
rl_ai_service = ReinforcementLearningAI()

@ai_bp.route('/providers', methods=['GET'])
def list_ai_providers():
    """
    List all configured AI providers
    """
    try:
        providers = ai_provider_service.list_providers()
        return jsonify({
            'providers': providers,
            'default_provider': ai_provider_service.default_provider
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/providers/<provider_name>/test', methods=['POST'])
def test_ai_provider(provider_name):
    """
    Test a specific AI provider
    """
    try:
        result = ai_provider_service.test_provider(provider_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/providers/<provider_name>/switch', methods=['POST'])
def switch_ai_provider(provider_name):
    """
    Switch the default AI provider
    """
    try:
        success = ai_provider_service.switch_provider(provider_name)
        if success:
            return jsonify({
                'message': f'Switched to provider: {provider_name}',
                'default_provider': ai_provider_service.default_provider
            })
        else:
            return jsonify({'error': f'Provider {provider_name} not available'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@ai_bp.route('/smart_chat', methods=['POST'])
def smart_chat():
    """Enhanced AI chat endpoint with conversation history and learning"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        session_id = data.get('session_id')
        context = data.get('context', {})
        use_vector_context = data.get('use_vector_context', False)  # Default to False for stability
        
        # Use enhanced AI service with vector database
        if use_vector_context:
            result = enhanced_ai_service.smart_chat_with_context(
                user_message=message, 
                session_id=session_id, 
                use_vector_context=True
            )
            
            return jsonify({
                'success': True,
                'response': result['response'],
                'session_id': session_id,
                'vector_context_used': result.get('vector_context_used', False),
                'similar_prompts_found': result.get('similar_prompts_found', 0),
                'relevant_context_found': result.get('relevant_context_found', 0),
                'business_knowledge_found': result.get('business_knowledge_found', 0),
                'response_time_ms': result.get('response_time', 0)
            })
        else:
            # Fallback to traditional service
            deepseek_service = DeepseekService()
            result = deepseek_service.smart_agent_response(message, session_id, context)
            
            return jsonify({
                'success': True,
                'response': result['response'],
                'session_id': result['session_id'],
                'intent_analysis': result.get('intent_analysis', {}),
                'response_time_ms': result.get('response_time_ms', 0),
                'context_used': result.get('context_used', False),
                'cached': result.get('cached', False)
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'response': "I encountered an error processing your request. Please try again."
        }), 500

@ai_bp.route('/conversation_history/<session_id>', methods=['GET'])
def get_conversation_history(session_id):
    """Get conversation history for a session"""
    try:
        limit = request.args.get('limit', 10, type=int)
        deepseek_service = DeepseekService()
        history = deepseek_service.get_conversation_history(session_id, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/popular_queries', methods=['GET'])
def get_popular_queries():
    """Get most popular queries for learning patterns"""
    try:
        limit = request.args.get('limit', 10, type=int)
        deepseek_service = DeepseekService()
        popular = deepseek_service.get_popular_queries(limit)
        
        return jsonify({
            'success': True,
            'popular_queries': popular
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

# ========================
# VECTOR DATABASE ENDPOINTS
# ========================

@ai_bp.route('/vector/prompt-suggestions', methods=['POST'])
def get_prompt_suggestions():
    """Get AI-powered prompt suggestions based on partial input"""
    try:
        data = request.get_json()
        partial_query = data.get('partial_query', '')
        n_suggestions = data.get('n_suggestions', 5)
        
        if not partial_query:
            return jsonify({'error': 'Partial query is required'}), 400
        
        suggestions = enhanced_ai_service.get_prompt_suggestions(partial_query, n_suggestions)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'partial_query': partial_query
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/vector/store-prompt', methods=['POST'])
def store_effective_prompt():
    """Store an effective prompt for future reference"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        category = data.get('category', 'user_generated')
        effectiveness_score = data.get('effectiveness_score', 0.8)
        
        if not prompt:
            return jsonify({'error': 'Prompt text is required'}), 400
        
        success = enhanced_ai_service.store_effective_prompt(
            prompt=prompt,
            category=category,
            effectiveness_score=effectiveness_score
        )
        
        return jsonify({
            'success': success,
            'message': 'Prompt stored successfully' if success else 'Failed to store prompt'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/vector/business-knowledge', methods=['POST'])
def store_business_knowledge():
    """Store business knowledge in vector database"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        topic = data.get('topic', 'general')
        source = data.get('source', 'manual')
        knowledge_id = data.get('knowledge_id', f"knowledge_{hash(content)}")
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        success = enhanced_ai_service.vector_db.store_business_knowledge(
            knowledge_id=knowledge_id,
            content=content,
            topic=topic,
            source=source
        )
        
        return jsonify({
            'success': success,
            'knowledge_id': knowledge_id,
            'message': 'Business knowledge stored successfully' if success else 'Failed to store knowledge'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/vector/search-knowledge', methods=['POST'])
def search_business_knowledge():
    """Search business knowledge using semantic similarity"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        n_results = data.get('n_results', 5)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        results = enhanced_ai_service.vector_db.search_business_knowledge(query, n_results)
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'results_count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/vector/stats', methods=['GET'])
def get_vector_database_stats():
    """Get vector database statistics"""
    try:
        stats = enhanced_ai_service.vector_db.get_collection_stats()
        analysis = enhanced_ai_service.analyze_query_patterns()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/vector/initialize', methods=['POST'])
def initialize_vector_database():
    """Initialize vector database with business knowledge from MySQL"""
    try:
        success = enhanced_ai_service.initialize_business_knowledge()
        
        return jsonify({
            'success': success,
            'message': 'Vector database initialized with business knowledge' if success else 'Failed to initialize'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/vector/similar-prompts', methods=['POST'])
def find_similar_prompts():
    """Find prompts similar to the given query"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        n_results = data.get('n_results', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        similar_prompts = enhanced_ai_service.vector_db.find_similar_prompts(query, n_results)
        
        return jsonify({
            'success': True,
            'similar_prompts': similar_prompts,
            'query': query,
            'results_count': len(similar_prompts)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========================
# REINFORCEMENT LEARNING ENDPOINTS
# ========================

@ai_bp.route('/rl/chat', methods=['POST'])
def rl_enhanced_chat():
    """Reinforcement Learning enhanced chat with adaptive strategies"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        session_id = data.get('session_id')
        context = data.get('context', {})
        
        # Use RL-enhanced AI service
        result = rl_ai_service.smart_chat_with_rl(
            user_message=message,
            session_id=session_id,
            context=context
        )
        
        return jsonify({
            'success': True,
            'response': result['response'],
            'conversation_id': result['conversation_id'],
            'strategy_used': result.get('strategy_used'),
            'predicted_quality': result.get('predicted_quality'),
            'rl_enhanced': True,
            'needs_feedback': True,
            'response_time_ms': result.get('response_time_ms', 0)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'response': "I encountered an error. Please try again."
        }), 500

@ai_bp.route('/rl/feedback', methods=['POST'])
def process_rl_feedback():
    """Process user feedback for reinforcement learning"""
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        feedback = data.get('feedback', {})
        
        if not conversation_id:
            return jsonify({'error': 'Conversation ID is required'}), 400
        
        # Process feedback and update learning
        result = rl_ai_service.process_user_feedback(conversation_id, feedback)
        
        return jsonify({
            'success': True,
            'reward_calculated': result.get('reward_calculated'),
            'learning_updated': True,
            'analytics': result.get('analytics'),
            'recommendations': result.get('recommendations')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/rl/analytics', methods=['GET'])
def get_rl_analytics():
    """Get reinforcement learning analytics and performance metrics"""
    try:
        analytics = rl_ai_service.get_rl_analytics()
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/rl/optimize', methods=['POST'])
def optimize_rl_performance():
    """Perform reinforcement learning optimization"""
    try:
        result = rl_ai_service.optimize_performance()
        
        return jsonify({
            'success': True,
            'optimization_result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/rl/strategies', methods=['GET'])
def get_response_strategies():
    """Get current response strategies and their performance weights"""
    try:
        analytics = rl_ai_service.get_rl_analytics()
        
        return jsonify({
            'success': True,
            'strategies': analytics.get('response_strategies', {}),
            'learning_progress': analytics.get('learning_progress', {}),
            'recommendations': analytics.get('recommendations', [])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/rl/predict-quality', methods=['POST'])
def predict_response_quality():
    """Predict expected response quality for a given prompt"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        context = data.get('context', {})
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Extract features and predict quality
        features = rl_ai_service._extract_prompt_features(user_message, context)
        predicted_quality = rl_ai_service.reward_system.predict_response_quality(features)
        strategy = rl_ai_service._select_response_strategy(user_message, predicted_quality)
        
        return jsonify({
            'success': True,
            'predicted_quality': predicted_quality,
            'recommended_strategy': strategy,
            'prompt_features': {
                'complexity_score': features.get('complexity_score'),
                'message_length': features.get('message_length'),
                'word_count': features.get('word_count')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500