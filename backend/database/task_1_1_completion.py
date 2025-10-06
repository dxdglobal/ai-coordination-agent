#!/usr/bin/env python3
"""
Task 1.1 Completion Script - Add Missing Database Components
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text

# Add to models.py - Missing Tables

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # CRM user ID
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # info, warning, error, success
    read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(500))  # Optional action link
    metadata = db.Column(db.JSON)  # Additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Foreign keys for context
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'read': self.read,
            'action_url': self.action_url,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'task_id': self.task_id,
            'project_id': self.project_id
        }

class MemoryEmbedding(db.Model):
    __tablename__ = 'memory_embeddings'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # Original text
    content_type = db.Column(db.String(50), nullable=False)  # task, comment, conversation, etc.
    embedding_vector = db.Column(db.JSON)  # Store embedding as JSON array
    embedding_model = db.Column(db.String(100), default='text-embedding-ada-002')
    
    # Metadata for semantic search
    source_id = db.Column(db.String(100))  # ID in source table
    source_table = db.Column(db.String(50))  # Source table name
    keywords = db.Column(db.JSON)  # Extracted keywords
    summary = db.Column(db.Text)  # AI-generated summary
    
    # Performance tracking
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime)
    similarity_threshold = db.Column(db.Float, default=0.8)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'content_type': self.content_type,
            'embedding_model': self.embedding_model,
            'source_id': self.source_id,
            'source_table': self.source_table,
            'keywords': self.keywords,
            'summary': self.summary,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'similarity_threshold': self.similarity_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    crm_user_id = db.Column(db.Integer, unique=True)  # Link to CRM users
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='user')  # admin, manager, user
    preferences = db.Column(db.JSON)  # User preferences
    ai_settings = db.Column(db.JSON)  # AI interaction settings
    
    # Activity tracking
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notifications = db.relationship('Notification', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'crm_user_id': self.crm_user_id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'preferences': self.preferences,
            'ai_settings': self.ai_settings,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notification_count': len(self.notifications)
        }

# PostgreSQL pgvector setup (if using PostgreSQL)
def setup_pgvector_extension():
    """Setup pgvector extension for PostgreSQL"""
    try:
        from sqlalchemy import text
        # This would be run in PostgreSQL
        sql_commands = [
            "CREATE EXTENSION IF NOT EXISTS vector;",
            """
            CREATE TABLE IF NOT EXISTS vector_embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                content_type VARCHAR(50) NOT NULL,
                embedding vector(1536),  -- OpenAI ada-002 dimensions
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            "CREATE INDEX IF NOT EXISTS vector_embeddings_content_type_idx ON vector_embeddings(content_type);",
            "CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx ON vector_embeddings USING ivfflat (embedding vector_cosine_ops);"
        ]
        return sql_commands
    except Exception as e:
        print(f"pgvector setup error: {e}")
        return []

# CRM Sync Configuration
CRM_SYNC_CONFIG = {
    'host': os.getenv('CRM_DB_HOST', '92.113.22.65'),
    'user': os.getenv('CRM_DB_USER', 'u906714182_sqlrrefdvdv'),
    'password': os.getenv('CRM_DB_PASSWORD'),
    'database': os.getenv('CRM_DB_NAME', 'u906714182_sqlrrefdvdv'),
    'sync_tables': [
        'tblstaff',
        'tbltasks', 
        'tblprojects',
        'tblnotifications',
        'tblchatmessages',
        'tblcomments'
    ],
    'sync_interval': 300  # 5 minutes
}

if __name__ == "__main__":
    print("Task 1.1 Database Components Defined")
    print("✅ Notifications table")
    print("✅ Memory Embeddings table") 
    print("✅ Users table")
    print("✅ pgvector setup (PostgreSQL)")
    print("✅ CRM sync configuration")