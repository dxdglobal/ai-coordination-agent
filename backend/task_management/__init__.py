"""
Task Management AI System

A comprehensive Flask backend that integrates:
- 🧠 NLP for intent detection
- 🔑 OpenAI GPT-4o for reasoning and summarization  
- 🗄️ MySQL CRM database integration
- 🧩 RAG with OpenAI embeddings + Chroma/FAISS
- 👥 CRM staff integration
- ⏰ Automated scheduling and reporting

Structure:
- config.py: Configuration and constants
- nlp_utils.py: Intent detection + name extraction  
- retriever.py: MySQL queries + vector index build/retrieval
- generator.py: OpenAI response generation (GPT-4o)
- scheduler.py: Daily AI summary job
- crm_connector.py: CRM API / MySQL interface for staff table
- logger.py: Central logging + error tracking
"""

"""
Task Management AI System

A comprehensive Flask backend that integrates:
- 🧠 NLP for intent detection
- 🔑 OpenAI GPT-4o for reasoning and summarization  
- 🗄️ MySQL CRM database integration
- 🧩 RAG with OpenAI embeddings + Chroma/FAISS
- 👥 CRM staff integration
- ⏰ Automated scheduling and reporting

Structure:
- config.py: Configuration and constants
- nlp_utils.py: Intent detection + name extraction  
- retriever.py: MySQL queries + vector index build/retrieval
- generator.py: OpenAI response generation (GPT-4o)
- scheduler.py: Daily AI summary job
- crm_connector.py: CRM API / MySQL interface for staff table
- logger.py: Central logging + error tracking
- rag_routes.py: Flask API routes for RAG endpoints
"""

# Import RAG components
from .config import Config
from .logger import get_logger, log_info, log_warning, log_error
from .crm_connector import get_crm_connector, CRMConnector
from .nlp_utils import get_nlp_processor, NLPProcessor
from .retriever import get_task_retriever, TaskRetriever
from .generator import get_response_generator, TaskResponseGenerator
from .scheduler import get_task_scheduler, start_scheduler, stop_scheduler

# Import API routes
from .rag_routes import rag_bp

# Main RAG pipeline function
def process_task_query(query: str) -> dict:
    """
    Main RAG pipeline for processing task management queries
    
    Flow: User Query → NLP (intent + name) → CRM (resolve staff ID) 
          → Retriever (MySQL + Chroma context) → OpenAI GPT-4o generation → JSON Response
    
    Args:
        query: Natural language query about tasks
        
    Returns:
        Structured response dictionary
    """
    try:
        # Step 1: NLP processing
        nlp_processor = get_nlp_processor()
        nlp_result = nlp_processor.process_query(query)
        
        if not nlp_result['is_actionable']:
            return {
                'success': True,
                'response_type': 'greeting',
                'message': "Hello! I can help you with task management. Try asking about task lists, summaries, or performance reports.",
                'nlp_result': nlp_result
            }
        
        if not nlp_result['employee_id']:
            return {
                'success': False,
                'error': 'Could not identify employee in query',
                'message': 'Please specify which employee you\'re asking about.',
                'nlp_result': nlp_result
            }
        
        # Step 2: Retrieve task data
        retriever = get_task_retriever()
        retrieved_data = retriever.retrieve_tasks_for_employee(
            employee_id=nlp_result['employee_id'],
            intent=nlp_result['intent'],
            query=query
        )
        
        if retrieved_data.get('error'):
            return {
                'success': False,
                'error': retrieved_data['error'],
                'nlp_result': nlp_result
            }
        
        # Step 3: Generate AI response
        generator = get_response_generator()
        ai_response = generator.generate_response(
            intent=nlp_result['intent'],
            employee=nlp_result['employee'],
            retrieved_data=retrieved_data,
            original_query=query
        )
        
        if ai_response.get('error'):
            return {
                'success': False,
                'error': ai_response['error'],
                'nlp_result': nlp_result,
                'retrieved_data': retrieved_data
            }
        
        # Step 4: Return structured response
        return {
            'success': True,
            'nlp_result': nlp_result,
            'retrieved_data': {
                'method': retrieved_data.get('retrieval_method'),
                'task_count': retrieved_data.get('total_count', 0)
            },
            'ai_response': ai_response
        }
        
    except Exception as e:
        logger = get_logger()
        logger.error("Failed to process task query", error=e, extra_data={'query': query})
        return {
            'success': False,
            'error': str(e),
            'query': query
        }

# Initialize system on import
def initialize_system():
    """Initialize the task management system"""
    try:
        # Validate configuration
        Config.validate_config()
        
        # Initialize core components
        logger = get_logger()
        logger.info("Task Management AI System initialized")
        
        # Start scheduler
        start_scheduler()
        logger.info("Task scheduler started")
        
        return True
        
    except Exception as e:
        logger = get_logger()
        logger.error("Failed to initialize task management system", error=e)
        return False

# Auto-initialize when module is imported
_initialized = initialize_system()

__all__ = [
    'Config',
    'get_logger', 'log_info', 'log_warning', 'log_error',
    'get_crm_connector', 'CRMConnector',
    'get_nlp_processor', 'NLPProcessor', 
    'get_task_retriever', 'TaskRetriever',
    'get_response_generator', 'TaskResponseGenerator',
    'get_task_scheduler', 'start_scheduler', 'stop_scheduler',
    'rag_bp',
    'process_task_query'
]

# Main RAG pipeline function
def process_task_query(query: str) -> dict:
    """
    Main RAG pipeline for processing task management queries
    
    Flow: User Query → NLP (intent + name) → CRM (resolve staff ID) 
          → Retriever (MySQL + Chroma context) → OpenAI GPT-4o generation → JSON Response
    
    Args:
        query: Natural language query about tasks
        
    Returns:
        Structured response dictionary
    """
    try:
        # Step 1: NLP processing
        nlp_processor = get_nlp_processor()
        nlp_result = nlp_processor.process_query(query)
        
        if not nlp_result['is_actionable']:
            return {
                'success': True,
                'response_type': 'greeting',
                'message': "Hello! I can help you with task management. Try asking about task lists, summaries, or performance reports.",
                'nlp_result': nlp_result
            }
        
        if not nlp_result['employee_id']:
            return {
                'success': False,
                'error': 'Could not identify employee in query',
                'message': 'Please specify which employee you\'re asking about.',
                'nlp_result': nlp_result
            }
        
        # Step 2: Retrieve task data
        retriever = get_task_retriever()
        retrieved_data = retriever.retrieve_tasks_for_employee(
            employee_id=nlp_result['employee_id'],
            intent=nlp_result['intent'],
            query=query
        )
        
        if retrieved_data.get('error'):
            return {
                'success': False,
                'error': retrieved_data['error'],
                'nlp_result': nlp_result
            }
        
        # Step 3: Generate AI response
        generator = get_response_generator()
        ai_response = generator.generate_response(
            intent=nlp_result['intent'],
            employee=nlp_result['employee'],
            retrieved_data=retrieved_data,
            original_query=query
        )
        
        if ai_response.get('error'):
            return {
                'success': False,
                'error': ai_response['error'],
                'nlp_result': nlp_result,
                'retrieved_data': retrieved_data
            }
        
        # Step 4: Return structured response
        return {
            'success': True,
            'nlp_result': nlp_result,
            'retrieved_data': {
                'method': retrieved_data.get('retrieval_method'),
                'task_count': retrieved_data.get('total_count', 0)
            },
            'ai_response': ai_response
        }
        
    except Exception as e:
        logger = get_logger()
        logger.error("Failed to process task query", error=e, extra_data={'query': query})
        return {
            'success': False,
            'error': str(e),
            'query': query
        }

# Initialize system on import
def initialize_system():
    """Initialize the task management system"""
    try:
        # Validate configuration
        Config.validate_config()
        
        # Initialize core components
        logger = get_logger()
        logger.info("Task Management AI System initialized")
        
        # Start scheduler
        start_scheduler()
        logger.info("Task scheduler started")
        
        return True
        
    except Exception as e:
        logger = get_logger()
        logger.error("Failed to initialize task management system", error=e)
        return False

# Auto-initialize when module is imported
_initialized = initialize_system()

__all__ = [
    'Config',
    'get_logger', 'log_info', 'log_warning', 'log_error',
    'get_crm_connector', 'CRMConnector',
    'get_nlp_processor', 'NLPProcessor', 
    'get_task_retriever', 'TaskRetriever',
    'get_response_generator', 'TaskResponseGenerator',
    'get_task_scheduler', 'start_scheduler', 'stop_scheduler',
    'rag_bp',
    'process_task_query'
]