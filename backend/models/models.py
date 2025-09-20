from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SQLEnum

# Create db instance here to avoid circular imports
db = SQLAlchemy()

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'task_count': len(self.tasks)
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    priority = db.Column(SQLEnum(Priority), default=Priority.MEDIUM)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    assignee = db.Column(db.String(100))
    
    # Foreign Keys
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    
    # Relationships
    comments = db.relationship('Comment', backref='task', lazy=True, cascade='all, delete-orphan')
    labels = db.relationship('TaskLabel', backref='task', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'priority': self.priority.value if self.priority else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'assignee': self.assignee,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'labels': [label.to_dict() for label in self.labels],
            'comment_count': len(self.comments)
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'task_id': self.task_id
        }

class Label(db.Model):
    __tablename__ = 'labels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#007bff')  # Hex color code
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }

class TaskLabel(db.Model):
    __tablename__ = 'task_labels'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    label_id = db.Column(db.Integer, db.ForeignKey('labels.id'), nullable=False)
    
    # Relationships
    label = db.relationship('Label', backref='task_labels')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'label_id': self.label_id,
            'label': self.label.to_dict() if self.label else None
        }

class Integration(db.Model):
    __tablename__ = 'integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)  # zendesk, whatsapp, telegram, email, voice
    external_id = db.Column(db.String(200))  # External message/ticket ID
    content = db.Column(db.Text)
    sender = db.Column(db.String(100))
    recipient = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    meta_data = db.Column(db.JSON)  # Store additional platform-specific data
    
    # Optional link to task/project
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'external_id': self.external_id,
            'content': self.content,
            'sender': self.sender,
            'recipient': self.recipient,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.meta_data,
            'task_id': self.task_id,
            'project_id': self.project_id
        }

class AIAction(db.Model):
    __tablename__ = 'ai_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    action_type = db.Column(db.String(50))  # comment, assign, update_status, create_task
    target_type = db.Column(db.String(50))  # task, project
    target_id = db.Column(db.Integer)
    action_data = db.Column(db.JSON)  # Store action parameters
    executed = db.Column(db.Boolean, default=False)
    result = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'prompt': self.prompt,
            'action_type': self.action_type,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'action_data': self.action_data,
            'executed': self.executed,
            'result': self.result,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }

class ConversationHistory(db.Model):
    __tablename__ = 'conversation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100))  # Track conversation sessions
    user_query = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50))  # database_analytics, person_search, general_chat
    response_time_ms = db.Column(db.Integer)  # Response time in milliseconds
    confidence_score = db.Column(db.Float)  # AI confidence in response
    data_sources_used = db.Column(db.JSON)  # Which tables/sources were queried
    user_satisfaction = db.Column(db.Integer)  # User rating (1-5), optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_query': self.user_query,
            'ai_response': self.ai_response,
            'query_type': self.query_type,
            'response_time_ms': self.response_time_ms,
            'confidence_score': self.confidence_score,
            'data_sources_used': self.data_sources_used,
            'user_satisfaction': self.user_satisfaction,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PromptTemplate(db.Model):
    __tablename__ = 'prompt_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # analytics, person_search, task_management
    template = db.Column(db.Text, nullable=False)  # The prompt template with placeholders
    usage_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)  # Based on user satisfaction
    last_used = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'template': self.template,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AILearningPattern(db.Model):
    __tablename__ = 'ai_learning_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    query_pattern = db.Column(db.String(200), nullable=False)  # Pattern like "is {person} there"
    response_template = db.Column(db.Text, nullable=False)
    confidence_threshold = db.Column(db.Float, default=0.8)
    times_matched = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'query_pattern': self.query_pattern,
            'response_template': self.response_template,
            'confidence_threshold': self.confidence_threshold,
            'times_matched': self.times_matched,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }