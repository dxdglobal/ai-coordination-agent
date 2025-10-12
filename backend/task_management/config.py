"""
Configuration management for Task Management AI System
Handles database credentials, OpenAI API keys, and system constants
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class for the task management system"""
    
    # Database Configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'crm_database'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'charset': 'utf8mb4'
    }
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL_GPT = 'gpt-4o'
    OPENAI_MODEL_EMBEDDING = 'text-embedding-3-small'
    OPENAI_MAX_TOKENS = 4000
    OPENAI_TEMPERATURE = 0.2
    
    # Vector Database Configuration
    VECTOR_DB_TYPE = os.getenv('VECTOR_DB_TYPE', 'chroma')  # 'chroma' or 'faiss'
    CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
    FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'faiss_index')
    
    # NLP Configuration
    SPACY_MODEL = 'en_core_web_sm'
    INTENT_CONFIDENCE_THRESHOLD = 0.7
    
    # Intent Categories
    SUPPORTED_INTENTS = [
        'list_tasks',
        'task_summary', 
        'performance_report',
        'anomaly_check',
        'project_status',
        'employee_workload',
        'deadline_analysis'
    ]
    
    # Greeting patterns to ignore
    GREETING_PATTERNS = [
        r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
        r'\bhow are you\b',
        r'\bwhat\'s up\b',
        r'\bhow\'s it going\b'
    ]
    
    # Task Status Mapping (based on CRM database schema - 11 total statuses)
    TASK_STATUS_MAP = {
        1: 'Not Started',
        2: 'In Progress', 
        3: 'Testing',
        4: 'Awaiting Feedback',
        5: 'Completed',
        6: 'On Hold',
        7: 'Cancelled',
        8: 'Pending Review',
        9: 'Approved',
        10: 'Rejected',
        11: 'Archived'
    }
    
    # Task Priority Mapping
    TASK_PRIORITY_MAP = {
        1: 'Low',
        2: 'Medium',
        3: 'High', 
        4: 'Urgent'
    }
    
    # Scheduler Configuration
    SCHEDULER_TIMEZONE = 'UTC'
    DAILY_SUMMARY_TIME = '06:00'  # Run daily summaries at 6 AM UTC
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'task_management.log')
    
    # Performance Thresholds
    PERFORMANCE_THRESHOLDS = {
        'completion_rate_excellent': 90,
        'completion_rate_good': 75,
        'completion_rate_poor': 50,
        'overdue_threshold_warning': 5,
        'overdue_threshold_critical': 10
    }
    
    # Embedding Configuration
    EMBEDDING_BATCH_SIZE = 100
    EMBEDDING_DIMENSION = 1536  # text-embedding-3-small dimension
    TASK_PAGINATION_SIZE = 20
    
    # Cache Configuration
    CACHE_TTL_SECONDS = 3600  # 1 hour cache for employee data
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = ['OPENAI_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_database_url(cls):
        """Get SQLAlchemy database URL"""
        config = cls.DB_CONFIG
        return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"