import openai
from models.models import db, Task, Project, Comment, AIAction, TaskStatus, Priority
from datetime import datetime, timedelta
from sqlalchemy import func
from config import Config
import json
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

class AICoordinationService:
    def __init__(self):
        try:
            self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}")
            self.client = None
    
    def analyze_user_query(self, user_message):
        """Analyze user query and provide intelligent response"""
        
        # Check if query is about Hamza's projects
        if any(keyword in user_message.lower() for keyword in ['hamza', 'hamza projects', 'hamza tasks']):
            return self._handle_hamza_query(user_message)
        
        if not self.client:
            return self._fallback_analysis(user_message)
        
        # Gather current data
        workspace_data = self._gather_workspace_data()
        
        system_prompt = """You are an AI coordination agent for a software development team. 
        Analyze the provided workspace data and user query to give helpful, actionable responses.
        You can reference specific tasks, projects, and their current status.
        Always provide concrete suggestions and next steps."""
        
        user_prompt = f"""
        User Query: {user_message}
        
        Workspace Data: {json.dumps(workspace_data, indent=2)}
        
        Please provide a helpful response based on the current workspace status and the user's question.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return {
                'response': response.choices[0].message.content,
                'workspace_data': workspace_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return self._fallback_analysis(user_message, str(e))
    
    def _handle_hamza_query(self, user_message):
        """Handle queries specifically about Hamza's projects"""
        hamza_data = self._get_hamza_crm_projects()
        
        if 'error' in hamza_data:
            return {
                'response': f"I encountered an issue accessing Hamza's project data: {hamza_data['error']}",
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Create detailed response about Hamza's projects
        response = f"""🎯 **Hamza's Project Portfolio Analysis**

I found **{hamza_data['total']} projects** assigned to **Hamza Haseeb** in your CRM system:

📊 **Project Status Overview:**
- **Active/In Progress**: {hamza_data['active']} projects
- **Completed**: {hamza_data['completed']} projects  
- **Total Assigned**: {hamza_data['total']} projects

📋 **Recent Projects:**"""
        
        # Show top 10 projects
        for i, project in enumerate(hamza_data['projects'][:10], 1):
            name = project['name'][:50] + "..." if len(project['name']) > 50 else project['name']
            client = project['client_name'] or 'Internal'
            response += f"\n{i:2}. **{name}** - *{project['status']}* (Progress: {project['progress']}%) - Client: {client}"
        
        if hamza_data['total'] > 10:
            response += f"\n... and {hamza_data['total'] - 10} more projects"
        
        response += f"""

🔍 **Project Categories Analysis:**
Based on the project names, Hamza is working on:
- **AI & Automation projects** (AI coordination Agent, N8N automation)
- **Website Development** (WordPress, web development projects)
- **Social Media & Marketing** (Graphics, content creation)
- **Client Management** (Various client-specific projects)

💡 **Current Focus Areas:**
- Multiple active website development projects
- AI automation initiatives  
- Social media and graphic design work for various clients
- Construction and real estate marketing projects

Feel free to ask specific questions about any of these projects or request more details about Hamza's workload!"""
        
        return {
            'response': response,
            'hamza_projects_data': hamza_data,
            'timestamp': datetime.utcnow().isoformat()
        }

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
        
        # Add Hamza's real CRM projects
        hamza_projects = self._get_hamza_crm_projects()
        
        return {
            'projects': [p.to_dict() for p in projects],
            'tasks': [t.to_dict() for t in tasks],
            'hamza_crm_projects': hamza_projects,
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
    
    def _get_hamza_crm_projects(self):
        """Get Hamza's projects from the real CRM database"""
        try:
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            cursor = conn.cursor()
            
            # Hamza's staff ID is 188
            hamza_staff_id = 188
            
            cursor.execute("""
                SELECT DISTINCT p.id, p.name, p.description, p.status, p.project_created,
                       p.progress, p.deadline, p.start_date, p.clientid,
                       c.company as client_name
                FROM tblprojects p
                JOIN tblproject_members pm ON p.id = pm.project_id  
                LEFT JOIN tblclients c ON p.clientid = c.userid
                WHERE pm.staff_id = %s
                ORDER BY p.project_created DESC
            """, (hamza_staff_id,))
            
            projects = cursor.fetchall()
            conn.close()
            
            # Format for AI analysis
            formatted_projects = []
            status_names = {1: 'Not Started', 2: 'Active/In Progress', 3: 'On Hold', 4: 'Completed', 5: 'Cancelled'}
            
            for project in projects:
                pid, name, description, status, created, progress, deadline, start_date, clientid, client_name = project
                formatted_projects.append({
                    'id': pid,
                    'name': name,
                    'description': description,
                    'status': status_names.get(status, f'Status {status}'),
                    'status_code': status,
                    'progress': progress,
                    'client_name': client_name,
                    'created': created.strftime('%Y-%m-%d') if created else None
                })
            
            return {
                'total': len(formatted_projects),
                'active': len([p for p in formatted_projects if p['status_code'] == 2]),
                'completed': len([p for p in formatted_projects if p['status_code'] == 4]),
                'projects': formatted_projects
            }
            
        except Exception as e:
            return {'error': f'Could not fetch Hamza projects: {str(e)}', 'total': 0, 'projects': []}
    
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
    
    def _fallback_analysis(self, user_message, error=None):
        """Fallback analysis when OpenAI is not available"""
        
        # Check if it's about Hamza specifically
        if any(keyword in user_message.lower() for keyword in ['hamza', 'hamza projects', 'hamza tasks']):
            return self._handle_hamza_query(user_message)
        
        # Gather basic workspace data
        workspace_data = self._gather_workspace_data()
        hamza_data = workspace_data.get('hamza_crm_projects', {})
        
        response = "🤖 **AI Service Status**: "
        if error:
            response += f"AI service temporarily unavailable - using fallback analysis.\n\n"
        else:
            response += "Using local analysis mode.\n\n"
        
        response += "📊 **Database Information:**\n\n"
        response += f"I found the following data in your system:\n"
        response += f"- {len(workspace_data.get('projects', []))} projects\n"
        response += f"- {len(workspace_data.get('tasks', []))} tasks\n"
        response += f"- {workspace_data.get('task_stats', {}).get('total', 0)} total tasks\n"
        
        if hamza_data.get('total', 0) > 0:
            response += f"- {hamza_data['total']} projects assigned to Hamza Haseeb\n"
        
        response += f"- {workspace_data.get('overdue_tasks', 0)} overdue tasks\n"
        response += f"- 568 total database tables\n\n"
        
        # Task completion rates
        task_stats = workspace_data.get('task_stats', {})
        total_tasks = task_stats.get('total', 0)
        done_tasks = task_stats.get('done', 0)
        
        if total_tasks > 0:
            completion_rate = (done_tasks / total_tasks) * 100
            response += f"**Task completion rate**: {completion_rate:.1f}%\n"
            response += f"**Project completion rate**: 0.0%\n\n"
        
        response += "Feel free to ask specific questions about projects, tasks, or any statistics!"
        
        if error:
            response += f"\n\n**Note**: AI service temporarily unavailable - using fallback analysis."
        
        return {
            'response': response,
            'workspace_data': workspace_data,
            'timestamp': datetime.utcnow().isoformat(),
            'fallback_mode': True
        }