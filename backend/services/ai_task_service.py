from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import openai
import os
from models.models import db, Task, Project, TaskStatus, Priority
from services.vector_service import VectorDatabaseService

@dataclass
class TaskAnalysis:
    """Structure for AI-powered task analysis"""
    task_intent: str
    action_type: str  # create, update, delete, search, analyze
    task_data: Optional[Dict[str, Any]]
    filters: Optional[Dict[str, Any]]
    confidence: float
    suggestions: List[str]

class AITaskManagementService:
    """AI-powered task management service with intelligent operations"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        self.vector_service = VectorDatabaseService()
        
    async def process_task_query(self, query: str, user_context: Dict = None) -> Dict[str, Any]:
        """Process natural language task queries with AI intelligence"""
        try:
            # Analyze the query with AI
            analysis = await self._analyze_task_query(query)
            
            # Execute the appropriate action based on analysis
            result = await self._execute_task_action(analysis, user_context)
            
            return {
                'success': True,
                'action': analysis.action_type,
                'analysis': analysis,
                'result': result,
                'ai_response': await self._generate_response(query, analysis, result)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestions': [
                    'Try rephrasing your request',
                    'Be more specific about the task details',
                    'Check if you have permission for this action'
                ]
            }
    
    async def _analyze_task_query(self, query: str) -> TaskAnalysis:
        """Use AI to analyze and understand task-related queries"""
        try:
            prompt = f"""
            Analyze this task management query and extract the intent and required actions:
            
            Query: "{query}"
            
            Determine:
            1. What type of action is requested (create, update, delete, search, analyze, list)
            2. What task data is mentioned (title, description, assignee, priority, status, dates)
            3. What filters or conditions are specified
            4. The user's intent and confidence level
            
            Respond in JSON format:
            {{
                "task_intent": "brief description of what user wants",
                "action_type": "create|update|delete|search|analyze|list",
                "task_data": {{
                    "title": "extracted title if mentioned or generate appropriate title",
                    "description": "extracted description if mentioned or generate from context", 
                    "assignee": "extracted assignee if mentioned",
                    "priority": "low|medium|high|urgent if mentioned",
                    "status": "todo|in_progress|review|done|blocked if mentioned",
                    "due_date": "extracted date if mentioned"
                }},
                "filters": {{
                    "status": "filter by status if specified",
                    "assignee": "filter by assignee if specified",
                    "priority": "filter by priority if specified",
                    "project": "filter by project if specified",
                    "date_range": "filter by date range if specified"
                }},
                "confidence": 0.95,
                "suggestions": ["list of helpful suggestions"]
            }}
            
            Important: For CREATE actions, always generate a meaningful title and description based on the user's request.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            analysis_data = json.loads(response.choices[0].message.content)
            
            return TaskAnalysis(
                task_intent=analysis_data.get('task_intent', ''),
                action_type=analysis_data.get('action_type', 'search'),
                task_data=analysis_data.get('task_data'),
                filters=analysis_data.get('filters'),
                confidence=analysis_data.get('confidence', 0.7),
                suggestions=analysis_data.get('suggestions', [])
            )
            
        except Exception as e:
            # Fallback to pattern matching
            return self._fallback_analysis(query)
    
    def _fallback_analysis(self, query: str) -> TaskAnalysis:
        """Fallback analysis using pattern matching"""
        query_lower = query.lower()
        
        # Determine action type
        action_type = 'search'  # default
        if any(word in query_lower for word in ['create', 'add', 'new', 'make']):
            action_type = 'create'
        elif any(word in query_lower for word in ['update', 'edit', 'modify', 'change']):
            action_type = 'update'
        elif any(word in query_lower for word in ['delete', 'remove', 'cancel']):
            action_type = 'delete'
        elif any(word in query_lower for word in ['analyze', 'report', 'summary']):
            action_type = 'analyze'
        elif any(word in query_lower for word in ['list', 'show', 'find', 'search']):
            action_type = 'search'
        
        # Extract basic task data for creation
        task_data = None
        if action_type == 'create':
            # Generate title from query
            title = query.replace('create', '').replace('add', '').replace('new', '').replace('make', '').strip()
            if 'task for' in query_lower:
                title = query_lower.split('task for')[1].strip()
            elif 'task:' in query_lower:
                title = query_lower.split('task:')[1].strip()
            
            # Capitalize and clean title
            if title:
                title = title.replace('a ', '').replace('an ', '').strip().title()
            else:
                title = "New Task"
            
            task_data = {
                'title': title,
                'description': f"Task created from request: {query}",
                'status': 'todo',
                'priority': 'medium'
            }
        
        # Extract basic filters
        filters = {}
        if 'urgent' in query_lower:
            filters['priority'] = 'urgent'
        elif 'high priority' in query_lower:
            filters['priority'] = 'high'
        elif 'overdue' in query_lower:
            filters['overdue'] = True
        elif 'completed' in query_lower or 'done' in query_lower:
            filters['status'] = 'done'
        elif 'in progress' in query_lower:
            filters['status'] = 'in_progress'
        
        return TaskAnalysis(
            task_intent=f"User wants to {action_type} tasks",
            action_type=action_type,
            task_data=task_data,
            filters=filters,
            confidence=0.6,
            suggestions=['Try being more specific about the task details']
        )
    
    async def _execute_task_action(self, analysis: TaskAnalysis, user_context: Dict = None) -> Dict[str, Any]:
        """Execute the determined task action"""
        try:
            if analysis.action_type == 'create':
                return await self._create_task(analysis.task_data, user_context)
            elif analysis.action_type == 'search' or analysis.action_type == 'list':
                return await self._search_tasks(analysis.filters, user_context)
            elif analysis.action_type == 'analyze':
                return await self._analyze_tasks(analysis.filters, user_context)
            elif analysis.action_type == 'update':
                return await self._update_tasks(analysis.task_data, analysis.filters, user_context)
            elif analysis.action_type == 'delete':
                return await self._delete_tasks(analysis.filters, user_context)
            else:
                return await self._search_tasks(analysis.filters, user_context)
                
        except Exception as e:
            raise Exception(f"Failed to execute {analysis.action_type} action: {str(e)}")
    
    async def _create_task(self, task_data: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """Create a new task"""
        if not task_data or not task_data.get('title'):
            raise Exception("Task title is required to create a task")
        
        # Create new task
        task = Task(
            title=task_data.get('title'),
            description=task_data.get('description', ''),
            status=TaskStatus(task_data.get('status', 'todo')),
            priority=Priority(task_data.get('priority', 'medium')),
            assignee=task_data.get('assignee'),
            created_by=user_context.get('user_id') if user_context else None
        )
        
        # Handle due date
        if task_data.get('due_date'):
            try:
                task.end_time = datetime.fromisoformat(task_data['due_date'])
            except:
                pass
        
        db.session.add(task)
        db.session.commit()
        
        # Store in vector database
        try:
            self.vector_service.store_task_embedding(task.id, task.to_dict())
        except Exception as e:
            print(f"Warning: Failed to store task embedding: {e}")
        
        return {
            'created_task': task.to_dict(),
            'message': f"Successfully created task: {task.title}"
        }
    
    async def _search_tasks(self, filters: Dict = None, user_context: Dict = None) -> Dict[str, Any]:
        """Search and retrieve tasks based on filters"""
        query = Task.query
        
        # Apply filters
        if filters:
            if filters.get('status'):
                query = query.filter(Task.status == TaskStatus(filters['status']))
            if filters.get('priority'):
                query = query.filter(Task.priority == Priority(filters['priority']))
            if filters.get('assignee'):
                query = query.filter(Task.assignee == filters['assignee'])
            if filters.get('overdue'):
                query = query.filter(Task.end_time < datetime.utcnow())
        
        # Execute query
        tasks = query.limit(50).all()
        task_list = [task.to_dict() for task in tasks]
        
        # Calculate summary statistics
        total_tasks = len(task_list)
        completed_tasks = len([t for t in task_list if t['status'] == 'done'])
        overdue_tasks = len([t for t in task_list if t.get('end_time') and 
                           datetime.fromisoformat(t['end_time']) < datetime.utcnow()])
        
        return {
            'tasks': task_list,
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            'message': f"Found {total_tasks} tasks matching your criteria"
        }
    
    async def _analyze_tasks(self, filters: Dict = None, user_context: Dict = None) -> Dict[str, Any]:
        """Provide AI-powered analysis of tasks"""
        search_result = await self._search_tasks(filters, user_context)
        tasks = search_result['tasks']
        
        if not tasks:
            return {'message': 'No tasks found to analyze'}
        
        # Generate AI analysis
        try:
            prompt = f"""
            Analyze these tasks and provide insights:
            
            Tasks: {json.dumps(tasks[:10], indent=2)}
            
            Provide analysis on:
            1. Task distribution by status and priority
            2. Workload balance and bottlenecks
            3. Overdue items and risks
            4. Recommendations for improvement
            
            Format as a clear, actionable report.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.4
            )
            
            ai_analysis = response.choices[0].message.content
            
        except Exception as e:
            ai_analysis = f"AI analysis unavailable: {str(e)}"
        
        return {
            'tasks': tasks,
            'summary': search_result['summary'],
            'ai_analysis': ai_analysis,
            'message': f"Analysis complete for {len(tasks)} tasks"
        }
    
    async def _update_tasks(self, task_data: Dict, filters: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """Update existing tasks"""
        # Find tasks to update
        search_result = await self._search_tasks(filters, user_context)
        tasks_to_update = search_result['tasks']
        
        if not tasks_to_update:
            raise Exception("No tasks found matching the criteria")
        
        updated_count = 0
        for task_dict in tasks_to_update:
            task = Task.query.get(task_dict['id'])
            if task:
                # Update fields
                if task_data.get('status'):
                    task.status = TaskStatus(task_data['status'])
                if task_data.get('priority'):
                    task.priority = Priority(task_data['priority'])
                if task_data.get('assignee'):
                    task.assignee = task_data['assignee']
                
                task.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        
        return {
            'updated_count': updated_count,
            'message': f"Successfully updated {updated_count} tasks"
        }
    
    async def _delete_tasks(self, filters: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """Delete tasks (with safety checks)"""
        # Find tasks to delete
        search_result = await self._search_tasks(filters, user_context)
        tasks_to_delete = search_result['tasks']
        
        if not tasks_to_delete:
            raise Exception("No tasks found matching the criteria")
        
        # Safety check - don't delete too many tasks at once
        if len(tasks_to_delete) > 5:
            raise Exception("Too many tasks selected for deletion. Please be more specific.")
        
        deleted_count = 0
        for task_dict in tasks_to_delete:
            task = Task.query.get(task_dict['id'])
            if task:
                # Delete from vector database
                try:
                    self.vector_service.delete_task_embedding(task.id)
                except:
                    pass
                
                db.session.delete(task)
                deleted_count += 1
        
        db.session.commit()
        
        return {
            'deleted_count': deleted_count,
            'message': f"Successfully deleted {deleted_count} tasks"
        }
    
    async def _generate_response(self, query: str, analysis: TaskAnalysis, result: Dict) -> str:
        """Generate a natural language response"""
        try:
            prompt = f"""
            Generate a conversational response for this task management interaction:
            
            User Query: "{query}"
            Action Performed: {analysis.action_type}
            Result: {json.dumps(result, indent=2)[:1000]}
            
            Provide a helpful, conversational response that:
            1. Acknowledges what was done
            2. Summarizes key results
            3. Offers next steps or suggestions
            
            Keep it concise and user-friendly.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Fallback response
            if analysis.action_type == 'search':
                task_count = len(result.get('tasks', []))
                return f"I found {task_count} tasks matching your criteria. Would you like me to analyze them or help with any specific tasks?"
            elif analysis.action_type == 'create':
                return f"Successfully created the task! It's been added to your task list and is ready to be worked on."
            elif analysis.action_type == 'analyze':
                return f"I've analyzed your tasks and provided insights. Check the detailed analysis above for actionable recommendations."
            else:
                return f"Task {analysis.action_type} operation completed successfully!"

# Global service instance
ai_task_service = AITaskManagementService()