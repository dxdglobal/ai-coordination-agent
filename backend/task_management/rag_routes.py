"""
RAG API Routes for Task Management AI System
Flask routes: /ai/query, /ai/reindex, /ai/daily-summary
"""

from flask import Blueprint, request, jsonify
from .logger import get_logger
import time

# Create blueprint
rag_bp = Blueprint('rag', __name__, url_prefix='/ai')
logger = get_logger()

@rag_bp.route('/query', methods=['POST'])
def process_query():
    """
    Main RAG endpoint: POST /ai/query
    Body: { "query": "Summarize Hamza's AI tasks" }
    
    Flow: NLP → Intent → Retriever → Generator → JSON response
    """
    start_time = time.time()
    
    try:
        # Import locally to avoid circular imports
        from . import process_task_query
        
        # Get query from request
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter'
            }), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Empty query'
            }), 400
        
        # Process query through RAG pipeline
        result = process_task_query(query)
        
        # Add response metadata
        result['response_time'] = time.time() - start_time
        result['endpoint'] = '/ai/query'
        
        # Log performance
        logger.log_performance_metrics(
            '/ai/query', 
            result['response_time'], 
            200 if result['success'] else 400
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error("Error in /ai/query endpoint", error=e, 
                    extra_data={'query': request.get_json()})
        
        logger.log_performance_metrics('/ai/query', response_time, 500)
        
        return jsonify({
            'success': False,
            'error': str(e),
            'response_time': response_time
        }), 500

@rag_bp.route('/reindex', methods=['POST'])
def rebuild_embeddings():
    """
    Rebuild embedding index: POST /ai/reindex
    Optional body: { "employee_id": 123 } to reindex specific employee
    """
    start_time = time.time()
    
    try:
        # Get optional employee filter
        data = request.get_json() or {}
        employee_id = data.get('employee_id')
        
        # Rebuild embeddings (placeholder for when vector DB is ready)
        from .retriever import TaskRetriever
        from .config import Config
        
        retriever = TaskRetriever(Config())
        # result = retriever.build_embeddings_index(employee_id=employee_id)
        
        # For now, return a placeholder response
        result = {
            'success': True,
            'message': 'Reindexing completed (placeholder - vector DB not yet configured)',
            'employee_id': employee_id,
            'indexed_tasks': 0
        }
        
        # Add response metadata
        result['response_time'] = time.time() - start_time
        result['endpoint'] = '/ai/reindex'
        
        logger.info("Embeddings reindex completed", extra_data={
            'employee_id': employee_id,
            'success': result.get('success'),
            'indexed_count': result.get('indexed_count', 0)
        })
        
        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error("Error in /ai/reindex endpoint", error=e)
        
        return jsonify({
            'success': False,
            'error': str(e),
            'response_time': response_time
        }), 500

@rag_bp.route('/daily-summary', methods=['POST'])
def generate_daily_summary():
    """
    Generate daily summary: POST /ai/daily-summary
    Optional body: { "employee_id": 123 } for specific employee
    """
    start_time = time.time()
    
    try:
        # Get optional employee filter
        data = request.get_json() or {}
        employee_id = data.get('employee_id')
        
        # Run daily summary job (placeholder for when scheduler is ready)
        from .scheduler import TaskScheduler
        from .config import Config
        
        scheduler = TaskScheduler(Config())
        
        if employee_id:
            # Generate summary for specific employee (implement this method)
            result = {
                'success': False,
                'error': 'Single employee summary not yet implemented'
            }
        else:
            # Generate summaries for all employees (placeholder)
            # scheduler.generate_daily_summaries()
            result = {
                'success': True,
                'message': 'Daily summary generation completed (placeholder)',
                'summaries_generated': 0
            }
        
        # Add response metadata
        result['response_time'] = time.time() - start_time
        result['endpoint'] = '/ai/daily-summary'
        
        logger.info("Daily summary generation completed", extra_data={
            'employee_id': employee_id,
            'success': result.get('success')
        })
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error("Error in /ai/daily-summary endpoint", error=e)
        
        return jsonify({
            'success': False,
            'error': str(e),
            'response_time': response_time
        }), 500

@rag_bp.route('/test-queries', methods=['GET'])
def get_test_queries():
    """
    Get sample test queries: GET /ai/test-queries
    """
    test_queries = [
        {
            "query": "Show all tasks for Hamza",
            "intent": "list_tasks",
            "description": "List all active tasks assigned to Hamza"
        },
        {
            "query": "Summarize John's performance this week", 
            "intent": "performance_report",
            "description": "Generate performance analysis for John"
        },
        {
            "query": "What is Hamza working on?",
            "intent": "task_summary", 
            "description": "Get AI summary of Hamza's current tasks and focus areas"
        },
        {
            "query": "Check for issues in Sarah's tasks",
            "intent": "anomaly_check",
            "description": "Detect anomalies and problems in Sarah's task list"
        },
        {
            "query": "Compare Hamza's activity with last week",
            "intent": "performance_report",
            "description": "Performance comparison analysis"
        }
    ]
    
    return jsonify({
        'success': True,
        'test_queries': test_queries,
        'usage': 'Send any of these queries to POST /ai/query with body: {"query": "..."}'
    })

@rag_bp.route('/system-status', methods=['GET'])
def get_system_status():
    """
    Get system status: GET /ai/system-status
    """
    try:
        from task_management.crm_connector import get_crm_connector
        from task_management.retriever import get_task_retriever
        from task_management.scheduler import get_task_scheduler
        
        # Check components
        crm = get_crm_connector()
        retriever = get_task_retriever()
        scheduler = get_task_scheduler()
        
        # Get basic stats
        employees = crm.get_all_employees()
        scheduler_status = scheduler.get_job_status()
        
        status = {
            'success': True,
            'components': {
                'crm_connector': 'operational',
                'task_retriever': 'operational', 
                'scheduler': 'operational' if scheduler_status['scheduler_running'] else 'stopped',
                'vector_db': retriever.vector_db is not None
            },
            'stats': {
                'total_employees': len(employees),
                'scheduled_jobs': len(scheduler_status['jobs']),
                'sample_employees': [emp['full_name'] for emp in employees[:5]]  # Show first 5 employees
            },
            'scheduler': scheduler_status
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error("Error getting system status", error=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rag_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint: GET /ai/health"""
    return jsonify({
        'status': 'healthy',
        'service': 'Task Management RAG System',
        'timestamp': time.time()
    })

# Error handlers
@rag_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': [
            'POST /ai/query',
            'POST /ai/reindex', 
            'POST /ai/daily-summary',
            'GET /ai/test-queries',
            'GET /ai/system-status',
            'GET /ai/health'
        ]
    }), 404

@rag_bp.errorhandler(500)
def internal_error(error):
    logger.error("Internal server error in RAG API", error=error)
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500