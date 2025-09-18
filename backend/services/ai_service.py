import openai
from models.models import db, Task, Project, Comment, AIAction, TaskStatus, Priority
from datetime import datetime, timedelta
from sqlalchemy import func
from config import Config
import json

class AICoordinationService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
    
    def analyze_workspace(self, prompt):
        """Analyze the workspace based on a given prompt"""
        if not self.client:
            return {'error': 'OpenAI API key not configured'}
        
        # Gather workspace data
        workspace_data = self._gather_workspace_data()
        
        # Create analysis prompt
        analysis_prompt = f"""
        {prompt}
        
        Current workspace data:
        {json.dumps(workspace_data, indent=2)}
        
        Please analyze this workspace and provide:
        1. Current status overview
        2. Issues that need attention
        3. Recommended actions
        4. Priority adjustments needed
        5. Task assignments suggestions
        
        Format your response as JSON with these sections.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a project coordination AI assistant. Analyze the provided data and give actionable insights."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            analysis_result = response.choices[0].message.content
            
            # Store the analysis
            action = AIAction(
                prompt=prompt,
                action_type='analysis',
                result=analysis_result
            )
            db.session.add(action)
            db.session.commit()
            
            try:
                return json.loads(analysis_result)
            except json.JSONDecodeError:
                return {'raw_analysis': analysis_result}
                
        except Exception as e:
            return {'error': f'AI analysis failed: {str(e)}'}
    
    def chat(self, message):
        """Chat interface with AI agent"""
        if not self.client:
            return 'OpenAI API key not configured'
        
        workspace_data = self._gather_workspace_data()
        
        system_prompt = f"""
        You are a project coordination AI assistant. You have access to the current workspace data:
        {json.dumps(workspace_data, indent=2)}
        
        Help the user with project management tasks, provide insights, and suggest actions.
        You can reference specific tasks, projects, and their current status.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f'Chat failed: {str(e)}'
    
    def get_coordination_suggestions(self):
        """Get AI suggestions for improving coordination"""
        overdue_tasks = self._get_overdue_tasks()
        stalled_tasks = self._get_stalled_tasks()
        unassigned_tasks = self._get_unassigned_tasks()
        
        suggestions = []
        
        if overdue_tasks:
            suggestions.append({
                'type': 'overdue_tasks',
                'priority': 'high',
                'message': f'{len(overdue_tasks)} tasks are overdue and need immediate attention',
                'tasks': [task.to_dict() for task in overdue_tasks[:5]]
            })
        
        if stalled_tasks:
            suggestions.append({
                'type': 'stalled_tasks',
                'priority': 'medium',
                'message': f'{len(stalled_tasks)} tasks have been in progress for more than a week',
                'tasks': [task.to_dict() for task in stalled_tasks[:5]]
            })
        
        if unassigned_tasks:
            suggestions.append({
                'type': 'unassigned_tasks',
                'priority': 'medium',
                'message': f'{len(unassigned_tasks)} tasks need to be assigned',
                'tasks': [task.to_dict() for task in unassigned_tasks[:5]]
            })
        
        return suggestions
    
    def execute_action(self, action):
        """Execute a pending AI action"""
        try:
            if action.action_type == 'comment':
                self._execute_comment_action(action)
            elif action.action_type == 'assign':
                self._execute_assign_action(action)
            elif action.action_type == 'update_status':
                self._execute_status_update_action(action)
            elif action.action_type == 'create_task':
                self._execute_create_task_action(action)
            
            action.executed = True
            action.executed_at = datetime.utcnow()
            db.session.commit()
            
            return {'success': True, 'action': action.to_dict()}
            
        except Exception as e:
            action.result = f'Execution failed: {str(e)}'
            db.session.commit()
            return {'success': False, 'error': str(e)}
    
    def auto_assign_tasks(self, project_id=None):
        """Auto-assign tasks based on workload and skills"""
        query = Task.query.filter(Task.assignee.is_(None))
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        unassigned_tasks = query.all()
        
        # Simple assignment logic (can be enhanced with ML)
        assignees = ['dev1', 'dev2', 'dev3']  # Could be fetched from user management
        assignments = []
        
        for i, task in enumerate(unassigned_tasks):
            assignee = assignees[i % len(assignees)]
            task.assignee = assignee
            assignments.append({
                'task_id': task.id,
                'task_title': task.title,
                'assignee': assignee
            })
        
        db.session.commit()
        
        return {
            'success': True,
            'assigned_count': len(assignments),
            'assignments': assignments
        }
    
    def analyze_task_priorities(self, project_id=None):
        """Analyze and suggest task priority changes"""
        query = Task.query
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        tasks = query.all()
        suggestions = []
        
        for task in tasks:
            # Suggest priority increase for overdue tasks
            if task.end_time and task.end_time < datetime.utcnow() and task.status != TaskStatus.DONE:
                if task.priority != Priority.URGENT:
                    suggestions.append({
                        'task_id': task.id,
                        'task_title': task.title,
                        'current_priority': task.priority.value,
                        'suggested_priority': 'urgent',
                        'reason': 'Task is overdue'
                    })
            
            # Suggest priority increase for tasks in progress too long
            if (task.status == TaskStatus.IN_PROGRESS and 
                task.start_time and 
                task.start_time < datetime.utcnow() - timedelta(days=7)):
                if task.priority == Priority.LOW:
                    suggestions.append({
                        'task_id': task.id,
                        'task_title': task.title,
                        'current_priority': task.priority.value,
                        'suggested_priority': 'medium',
                        'reason': 'Task has been in progress for over a week'
                    })
        
        return {'suggestions': suggestions}
    
    def analyze_time_tracking(self):
        """Analyze time tracking data and provide insights"""
        # Get tasks with time tracking data
        tasks_with_time = Task.query.filter(
            Task.estimated_hours.isnot(None),
            Task.actual_hours.isnot(None)
        ).all()
        
        if not tasks_with_time:
            return {'message': 'No time tracking data available'}
        
        # Calculate statistics
        total_estimated = sum(t.estimated_hours for t in tasks_with_time)
        total_actual = sum(t.actual_hours for t in tasks_with_time)
        variance = total_actual - total_estimated
        
        overestimated = [t for t in tasks_with_time if t.actual_hours < t.estimated_hours * 0.8]
        underestimated = [t for t in tasks_with_time if t.actual_hours > t.estimated_hours * 1.2]
        
        return {
            'total_estimated_hours': total_estimated,
            'total_actual_hours': total_actual,
            'variance_hours': variance,
            'variance_percentage': (variance / total_estimated * 100) if total_estimated > 0 else 0,
            'overestimated_tasks': len(overestimated),
            'underestimated_tasks': len(underestimated),
            'accuracy_rate': len(tasks_with_time) - len(overestimated) - len(underestimated)
        }
    
    def _gather_workspace_data(self):
        """Gather current workspace data for AI analysis"""
        projects = Project.query.all()
        tasks = Task.query.all()
        
        return {
            'projects': [p.to_dict() for p in projects],
            'tasks': [t.to_dict() for t in tasks],
            'task_stats': {
                'total': len(tasks),
                'todo': len([t for t in tasks if t.status == TaskStatus.TODO]),
                'in_progress': len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
                'done': len([t for t in tasks if t.status == TaskStatus.DONE]),
                'blocked': len([t for t in tasks if t.status == TaskStatus.BLOCKED])
            },
            'overdue_tasks': len(self._get_overdue_tasks()),
            'unassigned_tasks': len(self._get_unassigned_tasks())
        }
    
    def _get_overdue_tasks(self):
        """Get tasks that are overdue"""
        return Task.query.filter(
            Task.end_time < datetime.utcnow(),
            Task.status != TaskStatus.DONE
        ).all()
    
    def _get_stalled_tasks(self):
        """Get tasks that have been in progress for too long"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        return Task.query.filter(
            Task.status == TaskStatus.IN_PROGRESS,
            Task.start_time < week_ago
        ).all()
    
    def _get_unassigned_tasks(self):
        """Get tasks without assignees"""
        return Task.query.filter(Task.assignee.is_(None)).all()
    
    def _execute_comment_action(self, action):
        """Execute a comment action"""
        data = action.action_data
        comment = Comment(
            content=data.get('content'),
            author='AI Agent',
            task_id=action.target_id
        )
        db.session.add(comment)
    
    def _execute_assign_action(self, action):
        """Execute an assign action"""
        task = Task.query.get(action.target_id)
        if task:
            task.assignee = action.action_data.get('assignee')
    
    def _execute_status_update_action(self, action):
        """Execute a status update action"""
        task = Task.query.get(action.target_id)
        if task:
            task.status = TaskStatus(action.action_data.get('status'))
    
    def _execute_create_task_action(self, action):
        """Execute a create task action"""
        data = action.action_data
        task = Task(
            title=data.get('title'),
            description=data.get('description'),
            project_id=data.get('project_id'),
            priority=Priority(data.get('priority', 'medium'))
        )
        db.session.add(task)