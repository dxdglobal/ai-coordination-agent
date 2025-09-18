import openai
import json
from typing import List, Dict, Any
from models.models import Project, Task, Comment, Label, Integration, db
from sqlalchemy import or_, and_, text, inspect
import sqlalchemy

class DeepseekService:
    def __init__(self):
        # Configure for OpenAI API (the key was actually OpenAI, not Deepseek)
        try:
            self.client = openai.OpenAI(
                api_key="sk-b9f603a0e4a448efa936d1c1484fd108"
            )
            self.api_available = True
        except Exception as e:
            print(f"⚠️ OpenAI API not available: {str(e)}")
            self.client = None
            self.api_available = False
    
    def database_analytics(self, query: str) -> Dict[str, Any]:
        """
        Answer database analytics questions using AI
        Examples: "How many tables in database?", "Total projects?", "Show me all stats"
        """
        try:
            # Get database statistics
            db_stats = self._get_database_statistics()
            
            # Use AI to understand the question and provide appropriate answer
            ai_response = self._analyze_database_question(query, db_stats)
            
            return {
                'query': query,
                'answer': ai_response,
                'database_stats': db_stats,
                'timestamp': str(sqlalchemy.func.now())
            }
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'answer': f"I encountered an error while analyzing the database: {str(e)}"
            }
    
    def _get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            # Get table information
            inspector = inspect(db.engine)
            all_tables = inspector.get_table_names()
            
            # Count our main application tables
            project_count = Project.query.count()
            task_count = Task.query.count()
            comment_count = Comment.query.count()
            label_count = Label.query.count()
            integration_count = Integration.query.count()
            
            # Task status breakdown
            task_statuses = {}
            for status in ['todo', 'in_progress', 'review', 'done', 'blocked']:
                count = Task.query.filter(Task.status == status).count()
                task_statuses[status] = count
            
            # Task priority breakdown
            task_priorities = {}
            for priority in ['low', 'medium', 'high', 'urgent']:
                count = Task.query.filter(Task.priority == priority).count()
                task_priorities[priority] = count
            
            # Project status breakdown
            project_statuses = {}
            for status in ['todo', 'in_progress', 'review', 'done', 'blocked']:
                count = Project.query.filter(Project.status == status).count()
                project_statuses[status] = count
            
            # Recent activity
            recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
            recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
            recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
            
            # Integration platform breakdown
            integration_platforms = {}
            platforms = db.session.query(Integration.platform).distinct().all()
            for (platform,) in platforms:
                count = Integration.query.filter(Integration.platform == platform).count()
                integration_platforms[platform] = count
            
            return {
                'total_tables': len(all_tables),
                'table_names': all_tables,
                'application_tables': {
                    'projects': project_count,
                    'tasks': task_count,
                    'comments': comment_count,
                    'labels': label_count,
                    'integrations': integration_count
                },
                'task_analysis': {
                    'total_tasks': task_count,
                    'by_status': task_statuses,
                    'by_priority': task_priorities,
                    'completion_rate': (task_statuses.get('done', 0) / task_count * 100) if task_count > 0 else 0
                },
                'project_analysis': {
                    'total_projects': project_count,
                    'by_status': project_statuses,
                    'completion_rate': (project_statuses.get('done', 0) / project_count * 100) if project_count > 0 else 0
                },
                'integration_analysis': {
                    'total_integrations': integration_count,
                    'by_platform': integration_platforms
                },
                'recent_activity': {
                    'recent_tasks': [{'id': t.id, 'title': t.title, 'created_at': str(t.created_at)} for t in recent_tasks],
                    'recent_projects': [{'id': p.id, 'name': p.name, 'created_at': str(p.created_at)} for p in recent_projects],
                    'recent_comments': [{'id': c.id, 'author': c.author, 'created_at': str(c.created_at)} for c in recent_comments]
                }
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'message': 'Could not retrieve database statistics'
            }
    
    def _analyze_database_question(self, question: str, db_stats: Dict[str, Any]) -> str:
        """Use AI to answer database questions based on statistics"""
        try:
            # If API is not available, use fallback immediately
            if not self.api_available or not self.client:
                return self._generate_fallback_response(question, db_stats)
            
            # Format the database stats for AI
            stats_summary = f"""
            DATABASE STATISTICS:
            
            Total Tables: {db_stats.get('total_tables', 0)}
            All Tables: {', '.join(db_stats.get('table_names', [])[:20])}{'...' if len(db_stats.get('table_names', [])) > 20 else ''}
            
            APPLICATION DATA:
            - Total Projects: {db_stats.get('application_tables', {}).get('projects', 0)}
            - Total Tasks: {db_stats.get('application_tables', {}).get('tasks', 0)}
            - Total Comments: {db_stats.get('application_tables', {}).get('comments', 0)}
            - Total Labels: {db_stats.get('application_tables', {}).get('labels', 0)}
            - Total Integrations: {db_stats.get('application_tables', {}).get('integrations', 0)}
            
            TASK BREAKDOWN:
            - By Status: {db_stats.get('task_analysis', {}).get('by_status', {})}
            - By Priority: {db_stats.get('task_analysis', {}).get('by_priority', {})}
            - Task Completion Rate: {db_stats.get('task_analysis', {}).get('completion_rate', 0):.1f}%
            
            PROJECT BREAKDOWN:
            - By Status: {db_stats.get('project_analysis', {}).get('by_status', {})}
            - Project Completion Rate: {db_stats.get('project_analysis', {}).get('completion_rate', 0):.1f}%
            
            INTEGRATION BREAKDOWN:
            - By Platform: {db_stats.get('integration_analysis', {}).get('by_platform', {})}
            
            RECENT ACTIVITY:
            - Recent Tasks: {len(db_stats.get('recent_activity', {}).get('recent_tasks', []))} items
            - Recent Projects: {len(db_stats.get('recent_activity', {}).get('recent_projects', []))} items
            - Recent Comments: {len(db_stats.get('recent_activity', {}).get('recent_comments', []))} items
            """
            
            prompt = f"""
            You are a database analytics assistant for an AI Coordination Agent system. 
            Answer the user's question based on the database statistics provided.
            
            User Question: "{question}"
            
            {stats_summary}
            
            Please provide a comprehensive, helpful answer to the user's question based on this data. 
            Be specific with numbers and provide insights where relevant.
            If the user asks about tables, projects, tasks, or any statistics, use the exact numbers from the data above.
            Format your response in a clear, conversational way.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful database analytics assistant. Provide clear, accurate answers based on the database statistics provided. Always use the exact numbers from the data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback response using direct data analysis
            return self._generate_fallback_response(question, db_stats, str(e))
    
    def _generate_fallback_response(self, question: str, db_stats: Dict[str, Any], error: str = None) -> str:
        """Generate fallback response when AI service fails"""
        question_lower = question.lower()
        
        # Direct responses for common questions
        if 'how many tables' in question_lower or 'total tables' in question_lower:
            return f"📊 Database Analysis:\n\nThe database contains {db_stats.get('total_tables', 0)} tables in total.\n\nMain application tables:\n- Projects: {db_stats.get('application_tables', {}).get('projects', 0)}\n- Tasks: {db_stats.get('application_tables', {}).get('tasks', 0)}\n- Comments: {db_stats.get('application_tables', {}).get('comments', 0)}\n- Labels: {db_stats.get('application_tables', {}).get('labels', 0)}\n- Integrations: {db_stats.get('application_tables', {}).get('integrations', 0)}"
        
        elif 'total projects' in question_lower or 'how many projects' in question_lower:
            total_projects = db_stats.get('application_tables', {}).get('projects', 0)
            project_breakdown = db_stats.get('project_analysis', {}).get('by_status', {})
            breakdown_text = "\n".join([f"- {status.replace('_', ' ').title()}: {count}" for status, count in project_breakdown.items()])
            return f"📁 Project Analysis:\n\nTotal Projects: {total_projects}\n\nProject Status Breakdown:\n{breakdown_text}\n\nCompletion Rate: {db_stats.get('project_analysis', {}).get('completion_rate', 0):.1f}%"
        
        elif 'total tasks' in question_lower or 'how many tasks' in question_lower:
            total_tasks = db_stats.get('application_tables', {}).get('tasks', 0)
            task_breakdown = db_stats.get('task_analysis', {}).get('by_status', {})
            breakdown_text = "\n".join([f"- {status.replace('_', ' ').title()}: {count}" for status, count in task_breakdown.items()])
            return f"✅ Task Analysis:\n\nTotal Tasks: {total_tasks}\n\nTask Status Breakdown:\n{breakdown_text}\n\nCompletion Rate: {db_stats.get('task_analysis', {}).get('completion_rate', 0):.1f}%"
        
        elif 'completion rate' in question_lower:
            task_rate = db_stats.get('task_analysis', {}).get('completion_rate', 0)
            project_rate = db_stats.get('project_analysis', {}).get('completion_rate', 0)
            return f"📈 Completion Analysis:\n\nTask Completion Rate: {task_rate:.1f}%\nProject Completion Rate: {project_rate:.1f}%\n\nOverall Progress: {'Excellent' if task_rate > 75 else 'Good' if task_rate > 50 else 'Needs Attention'}"
        
        elif 'stats' in question_lower or 'analytics' in question_lower or 'overview' in question_lower:
            return f"""📊 Complete Database Analytics Overview:

🗄️ **Database Structure:**
- Total Tables: {db_stats.get('total_tables', 0)}

📋 **Application Data:**
- Projects: {db_stats.get('application_tables', {}).get('projects', 0)}
- Tasks: {db_stats.get('application_tables', {}).get('tasks', 0)}
- Comments: {db_stats.get('application_tables', {}).get('comments', 0)}
- Labels: {db_stats.get('application_tables', {}).get('labels', 0)}
- Integrations: {db_stats.get('application_tables', {}).get('integrations', 0)}

✅ **Task Performance:**
- Completion Rate: {db_stats.get('task_analysis', {}).get('completion_rate', 0):.1f}%
- Status Distribution: {db_stats.get('task_analysis', {}).get('by_status', {})}

📁 **Project Performance:**
- Completion Rate: {db_stats.get('project_analysis', {}).get('completion_rate', 0):.1f}%
- Status Distribution: {db_stats.get('project_analysis', {}).get('by_status', {})}

🔄 **Recent Activity:**
- Recent Tasks: {len(db_stats.get('recent_activity', {}).get('recent_tasks', []))}
- Recent Projects: {len(db_stats.get('recent_activity', {}).get('recent_projects', []))}
- Recent Comments: {len(db_stats.get('recent_activity', {}).get('recent_comments', []))}"""
        
        else:
            # Generic response with key stats
            return f"""📊 Database Information:

I found the following data in your system:
- {db_stats.get('application_tables', {}).get('projects', 0)} projects
- {db_stats.get('application_tables', {}).get('tasks', 0)} tasks  
- {db_stats.get('application_tables', {}).get('comments', 0)} comments
- {db_stats.get('total_tables', 0)} total database tables

Task completion rate: {db_stats.get('task_analysis', {}).get('completion_rate', 0):.1f}%
Project completion rate: {db_stats.get('project_analysis', {}).get('completion_rate', 0):.1f}%

Feel free to ask specific questions about projects, tasks, or any statistics!

{f'Note: AI service temporarily unavailable - using fallback analysis.' if error else ''}"""
    
    def intelligent_search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Perform intelligent search using Deepseek AI to understand user intent
        and search across projects, tasks, comments, and integrations
        """
        try:
            # First, use AI to understand search intent and extract keywords
            search_analysis = self._analyze_search_intent(query)
            
            # Perform database search based on AI analysis
            search_results = self._perform_database_search(search_analysis, limit)
            
            # Use AI to provide insights and summary
            ai_insights = self._generate_search_insights(query, search_results)
            
            return {
                'query': query,
                'search_analysis': search_analysis,
                'results': search_results,
                'ai_insights': ai_insights,
                'total_results': len(search_results)
            }
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'results': [],
                'total_results': 0
            }
    
    def _analyze_search_intent(self, query: str) -> Dict[str, Any]:
        """Use Deepseek AI to analyze search intent and extract relevant information"""
        try:
            prompt = f"""
            Analyze this search query for a project management system and extract relevant information:
            
            Query: "{query}"
            
            Please provide a JSON response with:
            1. intent: What is the user looking for? (project, task, status, person, time, integration, etc.)
            2. keywords: Array of important keywords to search for
            3. filters: Any specific filters mentioned (status, priority, dates, assignee, etc.)
            4. search_type: "exact", "fuzzy", or "semantic"
            5. categories: Which database tables to search (projects, tasks, comments, integrations)
            
            Example response:
            {{
                "intent": "find high priority tasks",
                "keywords": ["urgent", "high priority", "deadline"],
                "filters": {{"priority": "high", "status": "in_progress"}},
                "search_type": "semantic",
                "categories": ["tasks", "projects"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that helps analyze search queries for project management systems. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON, fallback if it fails
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback analysis
                return {
                    "intent": "general search",
                    "keywords": query.split(),
                    "filters": {},
                    "search_type": "fuzzy",
                    "categories": ["projects", "tasks", "comments", "integrations"]
                }
                
        except Exception as e:
            # Fallback analysis if AI fails
            return {
                "intent": "general search",
                "keywords": query.split(),
                "filters": {},
                "search_type": "fuzzy",
                "categories": ["projects", "tasks", "comments", "integrations"],
                "error": str(e)
            }
    
    def _perform_database_search(self, analysis: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Perform database search based on AI analysis"""
        results = []
        keywords = analysis.get('keywords', [])
        categories = analysis.get('categories', [])
        filters = analysis.get('filters', {})
        
        # Search Projects
        if 'projects' in categories:
            project_results = self._search_projects(keywords, filters, limit // 4)
            results.extend([{**proj, 'type': 'project'} for proj in project_results])
        
        # Search Tasks
        if 'tasks' in categories:
            task_results = self._search_tasks(keywords, filters, limit // 2)
            results.extend([{**task, 'type': 'task'} for task in task_results])
        
        # Search Comments
        if 'comments' in categories:
            comment_results = self._search_comments(keywords, limit // 4)
            results.extend([{**comment, 'type': 'comment'} for comment in comment_results])
        
        # Search Integrations
        if 'integrations' in categories:
            integration_results = self._search_integrations(keywords, limit // 4)
            results.extend([{**integration, 'type': 'integration'} for integration in integration_results])
        
        return results[:limit]
    
    def _search_projects(self, keywords: List[str], filters: Dict, limit: int) -> List[Dict]:
        """Search projects table"""
        query = Project.query
        
        # Text search
        if keywords:
            text_conditions = []
            for keyword in keywords:
                text_conditions.extend([
                    Project.name.ilike(f'%{keyword}%'),
                    Project.description.ilike(f'%{keyword}%')
                ])
            query = query.filter(or_(*text_conditions))
        
        # Apply filters
        if 'status' in filters:
            query = query.filter(Project.status == filters['status'])
        
        projects = query.limit(limit).all()
        return [project.to_dict() for project in projects]
    
    def _search_tasks(self, keywords: List[str], filters: Dict, limit: int) -> List[Dict]:
        """Search tasks table"""
        query = Task.query
        
        # Text search
        if keywords:
            text_conditions = []
            for keyword in keywords:
                text_conditions.extend([
                    Task.title.ilike(f'%{keyword}%'),
                    Task.description.ilike(f'%{keyword}%'),
                    Task.assignee.ilike(f'%{keyword}%')
                ])
            query = query.filter(or_(*text_conditions))
        
        # Apply filters
        if 'status' in filters:
            query = query.filter(Task.status == filters['status'])
        if 'priority' in filters:
            query = query.filter(Task.priority == filters['priority'])
        if 'assignee' in filters:
            query = query.filter(Task.assignee.ilike(f'%{filters["assignee"]}%'))
        
        tasks = query.limit(limit).all()
        return [task.to_dict() for task in tasks]
    
    def _search_comments(self, keywords: List[str], limit: int) -> List[Dict]:
        """Search comments table"""
        query = Comment.query
        
        if keywords:
            text_conditions = []
            for keyword in keywords:
                text_conditions.extend([
                    Comment.content.ilike(f'%{keyword}%'),
                    Comment.author.ilike(f'%{keyword}%')
                ])
            query = query.filter(or_(*text_conditions))
        
        comments = query.limit(limit).all()
        return [comment.to_dict() for comment in comments]
    
    def _search_integrations(self, keywords: List[str], limit: int) -> List[Dict]:
        """Search integrations table"""
        query = Integration.query
        
        if keywords:
            text_conditions = []
            for keyword in keywords:
                text_conditions.extend([
                    Integration.content.ilike(f'%{keyword}%'),
                    Integration.sender.ilike(f'%{keyword}%'),
                    Integration.platform.ilike(f'%{keyword}%')
                ])
            query = query.filter(or_(*text_conditions))
        
        integrations = query.limit(limit).all()
        return [integration.to_dict() for integration in integrations]
    
    def _generate_search_insights(self, original_query: str, results: List[Dict]) -> Dict[str, Any]:
        """Generate AI insights about the search results"""
        try:
            if not results:
                return {
                    "summary": "No results found for your search query.",
                    "suggestions": ["Try using different keywords", "Check spelling", "Broaden your search terms"]
                }
            
            # Prepare results summary for AI
            results_summary = []
            for result in results[:10]:  # Limit to first 10 for AI analysis
                result_type = result.get('type', 'unknown')
                if result_type == 'project':
                    results_summary.append(f"Project: {result.get('name', 'N/A')} - {result.get('status', 'N/A')}")
                elif result_type == 'task':
                    results_summary.append(f"Task: {result.get('title', 'N/A')} - {result.get('status', 'N/A')} - {result.get('priority', 'N/A')}")
                elif result_type == 'comment':
                    results_summary.append(f"Comment by {result.get('author', 'N/A')}: {result.get('content', 'N/A')[:50]}...")
                elif result_type == 'integration':
                    results_summary.append(f"Integration ({result.get('platform', 'N/A')}): {result.get('content', 'N/A')[:50]}...")
            
            prompt = f"""
            Analyze these search results for the query: "{original_query}"
            
            Results found ({len(results)} total):
            {chr(10).join(results_summary)}
            
            Please provide insights in JSON format:
            {{
                "summary": "Brief summary of what was found",
                "key_findings": ["key finding 1", "key finding 2", "key finding 3"],
                "suggestions": ["actionable suggestion 1", "suggestion 2"],
                "related_searches": ["related search 1", "related search 2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that provides insights about search results in project management systems. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=600
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "summary": f"Found {len(results)} results matching your search query.",
                    "key_findings": [f"Results include {len([r for r in results if r.get('type') == 'task'])} tasks, {len([r for r in results if r.get('type') == 'project'])} projects"],
                    "suggestions": ["Review the results to find what you're looking for"],
                    "related_searches": []
                }
                
        except Exception as e:
            return {
                "summary": f"Found {len(results)} results for your search.",
                "error": str(e),
                "suggestions": ["Review the search results above"],
                "related_searches": []
            }
    
    def chat_about_results(self, query: str, results: List[Dict], follow_up_question: str) -> str:
        """Allow users to ask follow-up questions about search results"""
        try:
            results_context = []
            for result in results[:5]:  # Limit context for better performance
                result_type = result.get('type', 'unknown')
                if result_type == 'project':
                    results_context.append(f"Project '{result.get('name')}': {result.get('description', 'N/A')}")
                elif result_type == 'task':
                    results_context.append(f"Task '{result.get('title')}': {result.get('description', 'N/A')} (Status: {result.get('status')}, Priority: {result.get('priority')})")
            
            prompt = f"""
            Original search: "{query}"
            
            Search results context:
            {chr(10).join(results_context)}
            
            User follow-up question: "{follow_up_question}"
            
            Please provide a helpful response based on the search results and context.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant helping users understand and work with project management search results. Be helpful and concise."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I'm sorry, I encountered an error while processing your question: {str(e)}"