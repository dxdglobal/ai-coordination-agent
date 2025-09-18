from app import db
from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SQLEnum

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
    metadata = db.Column(db.JSON)  # Store additional platform-specific data
    
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
            'metadata': self.metadata,
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