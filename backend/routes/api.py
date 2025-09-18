from flask import Blueprint, request, jsonify
from app import db
from models import Project, Task, Comment, Label, TaskLabel, TaskStatus, Priority
from datetime import datetime
from sqlalchemy import or_

api_bp = Blueprint('api', __name__)

# Projects endpoints
@api_bp.route('/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

@api_bp.route('/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    
    project = Project(
        name=data.get('name'),
        description=data.get('description'),
        status=TaskStatus(data.get('status', 'todo')),
        start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
        end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
        deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify(project.to_dict()), 201

@api_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.status = TaskStatus(data.get('status')) if data.get('status') else project.status
    project.start_date = datetime.fromisoformat(data['start_date']) if data.get('start_date') else project.start_date
    project.end_date = datetime.fromisoformat(data['end_date']) if data.get('end_date') else project.end_date
    project.deadline = datetime.fromisoformat(data['deadline']) if data.get('deadline') else project.deadline
    project.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(project.to_dict())

@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    
    return '', 204

# Tasks endpoints
@api_bp.route('/tasks', methods=['GET'])
def get_tasks():
    # Support filtering by project, status, assignee
    project_id = request.args.get('project_id')
    status = request.args.get('status')
    assignee = request.args.get('assignee')
    search = request.args.get('search')
    
    query = Task.query
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == TaskStatus(status))
    if assignee:
        query = query.filter(Task.assignee == assignee)
    if search:
        query = query.filter(or_(
            Task.title.contains(search),
            Task.description.contains(search)
        ))
    
    tasks = query.all()
    return jsonify([task.to_dict() for task in tasks])

@api_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    
    task = Task(
        title=data.get('title'),
        description=data.get('description'),
        status=TaskStatus(data.get('status', 'todo')),
        priority=Priority(data.get('priority', 'medium')),
        project_id=data.get('project_id'),
        assignee=data.get('assignee'),
        start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
        end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
        estimated_hours=data.get('estimated_hours'),
        actual_hours=data.get('actual_hours')
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify(task.to_dict()), 201

@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task():
    task_id = request.view_args['task_id']
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.status = TaskStatus(data.get('status')) if data.get('status') else task.status
    task.priority = Priority(data.get('priority')) if data.get('priority') else task.priority
    task.assignee = data.get('assignee', task.assignee)
    task.start_time = datetime.fromisoformat(data['start_time']) if data.get('start_time') else task.start_time
    task.end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else task.end_time
    task.estimated_hours = data.get('estimated_hours', task.estimated_hours)
    task.actual_hours = data.get('actual_hours', task.actual_hours)
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(task.to_dict())

@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    
    return '', 204

# Task status update endpoint
@api_bp.route('/tasks/<int:task_id>/status', methods=['PATCH'])
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    new_status = TaskStatus(data.get('status'))
    task.status = new_status
    task.updated_at = datetime.utcnow()
    
    # Auto-set start/end times based on status
    if new_status == TaskStatus.IN_PROGRESS and not task.start_time:
        task.start_time = datetime.utcnow()
    elif new_status == TaskStatus.DONE and not task.end_time:
        task.end_time = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(task.to_dict())

# Comments endpoints
@api_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
def get_task_comments(task_id):
    comments = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at.desc()).all()
    return jsonify([comment.to_dict() for comment in comments])

@api_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
def add_task_comment(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    comment = Comment(
        content=data.get('content'),
        author=data.get('author'),
        task_id=task_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify(comment.to_dict()), 201

# Labels endpoints
@api_bp.route('/labels', methods=['GET'])
def get_labels():
    labels = Label.query.all()
    return jsonify([label.to_dict() for label in labels])

@api_bp.route('/labels', methods=['POST'])
def create_label():
    data = request.get_json()
    
    label = Label(
        name=data.get('name'),
        color=data.get('color', '#007bff')
    )
    
    db.session.add(label)
    db.session.commit()
    
    return jsonify(label.to_dict()), 201

@api_bp.route('/tasks/<int:task_id>/labels', methods=['POST'])
def add_task_label(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    label_id = data.get('label_id')
    
    # Check if label is already assigned
    existing = TaskLabel.query.filter_by(task_id=task_id, label_id=label_id).first()
    if existing:
        return jsonify({'error': 'Label already assigned to task'}), 400
    
    task_label = TaskLabel(task_id=task_id, label_id=label_id)
    db.session.add(task_label)
    db.session.commit()
    
    return jsonify(task_label.to_dict()), 201

@api_bp.route('/tasks/<int:task_id>/labels/<int:label_id>', methods=['DELETE'])
def remove_task_label(task_id, label_id):
    task_label = TaskLabel.query.filter_by(task_id=task_id, label_id=label_id).first_or_404()
    db.session.delete(task_label)
    db.session.commit()
    
    return '', 204

# Statistics endpoints
@api_bp.route('/stats/overview', methods=['GET'])
def get_overview_stats():
    total_projects = Project.query.count()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status=TaskStatus.DONE).count()
    in_progress_tasks = Task.query.filter_by(status=TaskStatus.IN_PROGRESS).count()
    
    return jsonify({
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    })

@api_bp.route('/stats/projects/<int:project_id>', methods=['GET'])
def get_project_stats(project_id):
    project = Project.query.get_or_404(project_id)
    total_tasks = len(project.tasks)
    completed_tasks = len([t for t in project.tasks if t.status == TaskStatus.DONE])
    
    return jsonify({
        'project_id': project_id,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        'status_breakdown': {
            'todo': len([t for t in project.tasks if t.status == TaskStatus.TODO]),
            'in_progress': len([t for t in project.tasks if t.status == TaskStatus.IN_PROGRESS]),
            'review': len([t for t in project.tasks if t.status == TaskStatus.REVIEW]),
            'done': len([t for t in project.tasks if t.status == TaskStatus.DONE]),
            'blocked': len([t for t in project.tasks if t.status == TaskStatus.BLOCKED])
        }
    })