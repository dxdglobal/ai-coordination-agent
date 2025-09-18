import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')
    
    if DATABASE_TYPE == 'postgresql':
        password = quote_plus(os.environ.get('DB_PASSWORD', ''))
        SQLALCHEMY_DATABASE_URI = f"postgresql://{os.environ.get('DB_USER')}:{password}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT', 5432)}/{os.environ.get('DB_NAME')}"
    elif DATABASE_TYPE == 'mysql':
        password = quote_plus(os.environ.get('DB_PASSWORD', ''))
        SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{os.environ.get('DB_USER')}:{password}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT', 3306)}/{os.environ.get('DB_NAME')}"
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///project_management.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # External API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ZENDESK_API_TOKEN = os.environ.get('ZENDESK_API_TOKEN')
    ZENDESK_DOMAIN = os.environ.get('ZENDESK_DOMAIN')
    ZENDESK_EMAIL = os.environ.get('ZENDESK_EMAIL')
    
    # AI Provider Configurations
    AI_PROVIDERS = {
        "openai_primary": {
            "credential_name": "Main OpenAI Config",
            "credential_type": "openai",
            "description": "OpenAI API configuration",
            "openai_api_key": "sk-b9f603a0e4a448efa936d1c1484fd108",
            "openai_model": "gpt-4",
            "openai_organization": None,
            "environment": "production"
        }
    }
    
    # Default AI Provider
    DEFAULT_AI_PROVIDER = "openai_primary"
    
    # WhatsApp/Twilio
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    # Email
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))