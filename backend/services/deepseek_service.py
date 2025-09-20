import openai
import json
import time
import uuid
from typing import List, Dict, Any
from models.models import Project, Task, Comment, Label, Integration, ConversationHistory, PromptTemplate, AILearningPattern, db
from sqlalchemy import or_, and_, text, inspect
import sqlalchemy

class DeepseekService:
    def __init__(self):
        # Configure for OpenAI API (the key was actually OpenAI, not Deepseek)
        try:
            self.client = openai.OpenAI(
                api_key="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"
            )
            self.api_available = True
        except Exception as e:
            print(f"⚠️ OpenAI API not available: {str(e)}")
            self.client = None
            self.api_available = False
        
        # Session management for conversation tracking
        self.current_session_id = None
        self.conversation_context = []
    
    def start_new_session(self) -> str:
        """Start a new conversation session"""
        self.current_session_id = str(uuid.uuid4())
        self.conversation_context = []
        return self.current_session_id
    
    def get_or_create_session(self) -> str:
        """Get current session or create new one"""
        if not self.current_session_id:
            return self.start_new_session()
        return self.current_session_id
    
    def database_analytics(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """
        Answer database analytics questions using AI with conversation history tracking
        Examples: "How many tables in database?", "Total projects?", "Show me all stats"
        """
        start_time = time.time()
        
        try:
            # Get or create session
            if not session_id:
                session_id = self.get_or_create_session()
            
            # Check for similar queries in history for faster response
            similar_response = self._check_similar_queries(query)
            if similar_response:
                response = similar_response
                data_sources = ["cached_response"]
                query_type = "cached_analytics"
            else:
                # Get database statistics
                db_stats = self._get_database_statistics()
                
                # Use AI to understand the question and provide appropriate answer
                response = self._analyze_database_question(query, db_stats)
                data_sources = ["database_statistics", "ai_analysis"]
                query_type = "database_analytics"
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Save conversation history
            self._save_conversation_history(
                session_id=session_id,
                user_query=query,
                ai_response=response,
                query_type=query_type,
                response_time_ms=response_time_ms,
                data_sources_used=data_sources
            )
            
            # Add to conversation context
            self.conversation_context.append({
                'user': query,
                'assistant': response,
                'timestamp': time.time()
            })
            
            return {
                'query': query,
                'answer': response,
                'session_id': session_id,
                'response_time_ms': response_time_ms,
                'data_sources': data_sources,
                'timestamp': str(sqlalchemy.func.now())
            }
            
        except Exception as e:
            error_response = f"I encountered an error while analyzing the database: {str(e)}"
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Save error in history too
            self._save_conversation_history(
                session_id=session_id or self.get_or_create_session(),
                user_query=query,
                ai_response=error_response,
                query_type="error_response",
                response_time_ms=response_time_ms,
                data_sources_used=["error_handler"]
            )
            
            return {
                'query': query,
                'error': str(e),
                'answer': error_response,
                'session_id': session_id,
                'response_time_ms': response_time_ms
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
            
            # Count REAL business data from the actual database tables
            real_projects_count = 0
            real_tasks_count = 0
            real_staff_count = 0
            real_invoices_count = 0
            real_clients_count = 0
            try:
                # Count from tblprojects (the real projects table)
                result = db.session.execute(text("SELECT COUNT(*) FROM tblprojects"))
                real_projects_count = result.fetchone()[0]
                
                # Count from tbltasks (the real tasks table)
                result = db.session.execute(text("SELECT COUNT(*) FROM tbltasks"))
                real_tasks_count = result.fetchone()[0]
                
                # Count from tblstaff (employees/staff)
                result = db.session.execute(text("SELECT COUNT(*) FROM tblstaff"))
                real_staff_count = result.fetchone()[0]
                
                # Count from tblinvoices
                result = db.session.execute(text("SELECT COUNT(*) FROM tblinvoices"))
                real_invoices_count = result.fetchone()[0]
                
                # Count from tblclients
                result = db.session.execute(text("SELECT COUNT(*) FROM tblclients"))
                real_clients_count = result.fetchone()[0]
                
            except Exception as e:
                print(f"Note: Could not access real business tables: {e}")
            
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
                'real_business_data': {
                    'total_projects': real_projects_count,
                    'total_tasks': real_tasks_count,
                    'total_staff': real_staff_count,
                    'total_invoices': real_invoices_count,
                    'total_clients': real_clients_count,
                    'note': 'Data from actual business tables (tblprojects, tbltasks, tblstaff, tblinvoices, tblclients)'
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
                'real_project_analysis': {
                    'total_projects': real_projects_count,
                    'note': 'This is the actual project count from your business database'
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
            
            # Check for person-specific queries first
            if self._is_person_query(question):
                return self._handle_person_query(question)
            
            # Format the database stats for AI
            stats_summary = f"""
            DATABASE STATISTICS:
            
            Total Tables: {db_stats.get('total_tables', 0)}
            All Tables: {', '.join(db_stats.get('table_names', [])[:20])}{'...' if len(db_stats.get('table_names', [])) > 20 else ''}
            
            REAL BUSINESS DATA (Primary):
            - Total Projects: {db_stats.get('real_business_data', {}).get('total_projects', 0)} (from tblprojects)
            - Total Tasks: {db_stats.get('real_business_data', {}).get('total_tasks', 0)} (from tbltasks)
            - Total Staff/Employees: {db_stats.get('real_business_data', {}).get('total_staff', 0)} (from tblstaff)
            - Total Invoices: {db_stats.get('real_business_data', {}).get('total_invoices', 0)} (from tblinvoices)
            - Total Clients: {db_stats.get('real_business_data', {}).get('total_clients', 0)} (from tblclients)
            
            APPLICATION DATA (Secondary):
            - App Projects: {db_stats.get('application_tables', {}).get('projects', 0)}
            - App Tasks: {db_stats.get('application_tables', {}).get('tasks', 0)}
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
    
    def _is_person_query(self, question: str) -> bool:
        """Check if the question is asking about a specific person"""
        question_lower = question.lower()
        person_keywords = ['haseeb', 'is there', 'status of', 'tasks of', 'assigned to', 'working on']
        return any(keyword in question_lower for keyword in person_keywords)
    
    def _handle_person_query(self, question: str) -> str:
        """Handle person-specific queries by searching the database"""
        try:
            question_lower = question.lower()
            
            # Extract person name - look for common names or "haseeb" specifically
            person_name = None
            if 'haseeb' in question_lower:
                person_name = 'haseeb'
            # You can add more name extraction logic here
            
            if person_name:
                return self._search_person_in_database(person_name, question)
            else:
                return "Please specify the person's name you're asking about."
                
        except Exception as e:
            return f"I encountered an error while searching for person information: {str(e)}"
    
    def _search_person_in_database(self, person_name: str, original_question: str) -> str:
        """Search for a specific person across relevant database tables"""
        try:
            person_info = {}
            question_lower = original_question.lower()
            
            # Search in staff table
            staff_result = db.session.execute(text(f"""
                SELECT staffid, firstname, lastname, email, active, job_position, workplace 
                FROM tblstaff 
                WHERE LOWER(firstname) LIKE '%{person_name.lower()}%' 
                   OR LOWER(lastname) LIKE '%{person_name.lower()}%'
                   OR LOWER(email) LIKE '%{person_name.lower()}%'
                LIMIT 5
            """))
            staff_records = staff_result.fetchall()
            
            if staff_records:
                person_info['staff'] = [dict(row._mapping) for row in staff_records]
            
            # Search in task assignments
            if staff_records:
                staff_id = staff_records[0][0]  # Get first staff ID
                
                # Search for tasks assigned to this person
                task_result = db.session.execute(text(f"""
                    SELECT t.id, t.name, t.status, t.priority, t.startdate, t.duedate
                    FROM tbltasks t
                    JOIN tbltask_assigned ta ON t.id = ta.taskid
                    WHERE ta.staffid = {staff_id}
                    ORDER BY t.duedate DESC
                    LIMIT 10
                """))
                task_records = task_result.fetchall()
                
                if task_records:
                    person_info['tasks'] = [dict(row._mapping) for row in task_records]
            
            # Search in project members
            if staff_records:
                project_result = db.session.execute(text(f"""
                    SELECT p.id, p.name, p.status, pm.staff_id
                    FROM tblprojects p
                    JOIN tblproject_members pm ON p.id = pm.project_id
                    WHERE pm.staff_id = {staff_id}
                    LIMIT 10
                """))
                project_records = project_result.fetchall()
                
                if project_records:
                    person_info['projects'] = [dict(row._mapping) for row in project_records]
            
            # Generate response based on what was found and what was asked
            return self._format_person_response(person_name, person_info, original_question)
            
        except Exception as e:
            return f"I searched for '{person_name}' but encountered an error: {str(e)}. The person might not be in the database or there might be a connection issue."
    
    def _format_person_response(self, person_name: str, person_info: Dict, original_question: str) -> str:
        """Format the response about a person based on what was found"""
        if not person_info:
            return f"❌ **{person_name.title()} Not Found**\n\nI searched through the staff database but couldn't find anyone named '{person_name}'. They might not be in the system or the name might be spelled differently."
        
        response = f"👤 **Information about {person_name.title()}:**\n\n"
        
        # Staff information
        if 'staff' in person_info:
            staff = person_info['staff'][0]  # Take first match
            status = "✅ Active" if staff.get('active') == 1 else "❌ Inactive"
            response += f"**Staff Details:**\n"
            response += f"- Name: {staff.get('firstname', '')} {staff.get('lastname', '')}\n"
            response += f"- Email: {staff.get('email', 'N/A')}\n"
            response += f"- Status: {status}\n"
            response += f"- Staff ID: {staff.get('staffid', 'N/A')}\n"
            response += f"- Job Position ID: {staff.get('job_position', 'N/A')}\n"
            response += f"- Workplace ID: {staff.get('workplace', 'N/A')}\n\n"
        
        # Task information
        if 'tasks' in person_info:
            tasks = person_info['tasks']
            response += f"**📋 Current Tasks ({len(tasks)} found):**\n"
            for task in tasks[:5]:  # Show first 5 tasks
                status_emoji = {"1": "✅", "2": "🔄", "3": "⏸️", "4": "❌"}.get(str(task.get('status', '')), "📝")
                priority_emoji = {"1": "🔴", "2": "🟡", "3": "🔵", "4": "⚪"}.get(str(task.get('priority', '')), "📝")
                response += f"  {status_emoji} {task.get('name', 'Unnamed Task')} {priority_emoji}\n"
                if task.get('duedate'):
                    response += f"    Due: {task.get('duedate')}\n"
            response += "\n"
        
        # Project information
        if 'projects' in person_info:
            projects = person_info['projects']
            response += f"**📁 Current Projects ({len(projects)} found):**\n"
            for project in projects[:5]:  # Show first 5 projects
                status_emoji = {"1": "📝", "2": "🔄", "3": "⏸️", "4": "✅", "5": "❌"}.get(str(project.get('status', '')), "📁")
                response += f"  {status_emoji} {project.get('name', 'Unnamed Project')}\n"
            response += "\n"
        
        # Add specific answers based on the question
        question_lower = original_question.lower()
        if 'status' in question_lower:
            if 'staff' in person_info:
                status = "Active and working" if person_info['staff'][0].get('active') == 1 else "Inactive"
                response += f"**Current Status:** {status}\n"
        
        if not person_info.get('tasks') and 'task' in question_lower:
            response += "**Note:** No current tasks found assigned to this person.\n"
        
        return response
    
    def _generate_fallback_response(self, question: str, db_stats: Dict[str, Any], error: str = None) -> str:
        """Generate fallback response when AI service fails"""
        question_lower = question.lower()
        
        # Direct responses for common questions
        if 'how many tables' in question_lower or 'total tables' in question_lower:
            return f"📊 Database Analysis:\n\nThe database contains {db_stats.get('total_tables', 0)} tables in total.\n\nMain application tables:\n- Projects: {db_stats.get('application_tables', {}).get('projects', 0)}\n- Tasks: {db_stats.get('application_tables', {}).get('tasks', 0)}\n- Comments: {db_stats.get('application_tables', {}).get('comments', 0)}\n- Labels: {db_stats.get('application_tables', {}).get('labels', 0)}\n- Integrations: {db_stats.get('application_tables', {}).get('integrations', 0)}"
        
        elif 'total projects' in question_lower or 'how many projects' in question_lower:
            # Use the REAL business data count
            real_projects = db_stats.get('real_business_data', {}).get('total_projects', 0)
            app_projects = db_stats.get('application_tables', {}).get('projects', 0)
            
            if real_projects > 0:
                return f"📁 **REAL Project Count**: {real_projects} projects\n\n(This is from your actual business database table 'tblprojects')\n\nNote: There are also {app_projects} projects in the application demo table, but your real business data shows {real_projects} total projects."
            else:
                total_projects = app_projects
                project_breakdown = db_stats.get('project_analysis', {}).get('by_status', {})
                breakdown_text = "\n".join([f"- {status.replace('_', ' ').title()}: {count}" for status, count in project_breakdown.items()])
                return f"📁 Project Analysis:\n\nTotal Projects: {total_projects}\n\nProject Status Breakdown:\n{breakdown_text}\n\nCompletion Rate: {db_stats.get('project_analysis', {}).get('completion_rate', 0):.1f}%"
        
        elif 'total tasks' in question_lower or 'how many tasks' in question_lower:
            real_tasks = db_stats.get('real_business_data', {}).get('total_tasks', 0)
            app_tasks = db_stats.get('application_tables', {}).get('tasks', 0)
            
            if real_tasks > 0:
                return f"✅ **REAL Task Count**: {real_tasks} tasks\n\n(This is from your actual business database table 'tbltasks')\n\nNote: There are also {app_tasks} tasks in the application demo table, but your real business data shows {real_tasks} total tasks."
            else:
                total_tasks = app_tasks
                task_breakdown = db_stats.get('task_analysis', {}).get('by_status', {})
                breakdown_text = "\n".join([f"- {status.replace('_', ' ').title()}: {count}" for status, count in task_breakdown.items()])
                return f"✅ Task Analysis:\n\nTotal Tasks: {total_tasks}\n\nTask Status Breakdown:\n{breakdown_text}\n\nCompletion Rate: {db_stats.get('task_analysis', {}).get('completion_rate', 0):.1f}%"
        
        elif 'employee' in question_lower or 'staff' in question_lower or 'how many people' in question_lower:
            staff_count = db_stats.get('real_business_data', {}).get('total_staff', 0)
            return f"👥 **Staff/Employee Count**: {staff_count} employees\n\n(This is from your actual business database table 'tblstaff')\n\nThis includes all staff members in your system."
        
        elif 'invoice' in question_lower or 'billing' in question_lower:
            invoice_count = db_stats.get('real_business_data', {}).get('total_invoices', 0)
            return f"💰 **Invoice Count**: {invoice_count} invoices\n\n(This is from your actual business database table 'tblinvoices')\n\nThis includes all invoices in your system."
        
        elif 'client' in question_lower or 'customer' in question_lower:
            client_count = db_stats.get('real_business_data', {}).get('total_clients', 0)
            return f"🏢 **Client Count**: {client_count} clients\n\n(This is from your actual business database table 'tblclients')\n\nThis includes all clients in your system."
        
        elif self._is_person_query(question):
            return self._handle_person_query(question)
        
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
    
    def _save_conversation_history(self, session_id: str, user_query: str, ai_response: str, 
                                 query_type: str, response_time_ms: int, data_sources_used: List[str]):
        """Save conversation to database for learning and efficiency"""
        try:
            # Check if we're in an app context
            from flask import has_app_context
            if not has_app_context():
                print("Warning: Cannot save conversation history outside of app context")
                return
                
            conversation = ConversationHistory(
                session_id=session_id,
                user_query=user_query,
                ai_response=ai_response,
                query_type=query_type,
                response_time_ms=response_time_ms,
                data_sources_used=data_sources_used
            )
            db.session.add(conversation)
            db.session.commit()
        except Exception as e:
            print(f"Error saving conversation history: {e}")
            db.session.rollback()
    
    def _check_similar_queries(self, query: str) -> str:
        """Check if we have a recent similar query for faster response"""
        try:
            # Check if we're in an app context
            from flask import has_app_context
            if not has_app_context():
                return None
                
            # Look for exact or very similar queries in the last 24 hours
            recent_queries = ConversationHistory.query.filter(
                ConversationHistory.created_at >= sqlalchemy.func.date_sub(
                    sqlalchemy.func.now(), sqlalchemy.text('INTERVAL 24 HOUR')
                )
            ).filter(
                or_(
                    ConversationHistory.user_query == query,
                    ConversationHistory.user_query.like(f'%{query.lower()}%')
                )
            ).order_by(ConversationHistory.created_at.desc()).first()
            
            if recent_queries:
                return f"🔄 **Cached Response** (from recent query):\n\n{recent_queries.ai_response}"
            
            return None
        except Exception as e:
            print(f"Error checking similar queries: {e}")
            return None
    
    def get_conversation_history(self, session_id: str = None, limit: int = 10) -> List[Dict]:
        """Get conversation history for a session or recent conversations"""
        try:
            # Check if we're in an app context
            from flask import has_app_context
            if not has_app_context():
                return []
                
            query = ConversationHistory.query
            
            if session_id:
                query = query.filter(ConversationHistory.session_id == session_id)
            
            conversations = query.order_by(
                ConversationHistory.created_at.desc()
            ).limit(limit).all()
            
            return [conv.to_dict() for conv in conversations]
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def get_popular_queries(self, limit: int = 10) -> List[Dict]:
        """Get most popular queries for learning patterns"""
        try:
            # Check if we're in an app context
            from flask import has_app_context
            if not has_app_context():
                return []
                
            # Group by similar queries and count frequency
            popular = db.session.execute(text(f"""
                SELECT user_query, COUNT(*) as frequency, 
                       AVG(response_time_ms) as avg_response_time,
                       query_type
                FROM conversation_history 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY user_query 
                ORDER BY frequency DESC 
                LIMIT {limit}
            """)).fetchall()
            
            return [dict(row._mapping) for row in popular]
        except Exception as e:
            print(f"Error getting popular queries: {e}")
            return []
    
    def smart_agent_response(self, query: str, session_id: str = None, context: Dict = None) -> Dict[str, Any]:
        """
        Enhanced AI agent that can handle any type of business question intelligently
        Uses conversation history and context for better responses
        """
        start_time = time.time()
        
        try:
            # Get or create session
            if not session_id:
                session_id = self.get_or_create_session()
            
            # Check for similar queries first for efficiency
            cached_response = self._check_similar_queries(query)
            if cached_response:
                return {
                    'query': query,
                    'response': cached_response,
                    'session_id': session_id,
                    'cached': True,
                    'response_time_ms': int((time.time() - start_time) * 1000)
                }
            
            # Get conversation context for this session
            session_context = self.get_conversation_history(session_id, limit=5)
            
            # Determine query intent with context
            intent_analysis = self._analyze_query_intent(query, session_context, context)
            
            # Route to appropriate handler based on intent
            if intent_analysis['category'] == 'person_search':
                response = self._handle_person_query(query)
                query_type = 'person_search'
            elif intent_analysis['category'] == 'database_analytics':
                db_stats = self._get_database_statistics()
                response = self._analyze_database_question(query, db_stats)
                query_type = 'database_analytics'
            elif intent_analysis['category'] == 'task_management':
                response = self._handle_task_management_query(query, context)
                query_type = 'task_management'
            elif intent_analysis['category'] == 'business_intelligence':
                response = self._handle_business_intelligence_query(query)
                query_type = 'business_intelligence'
            else:
                response = self._handle_general_query(query, session_context)
                query_type = 'general_chat'
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Save conversation history
            self._save_conversation_history(
                session_id=session_id,
                user_query=query,
                ai_response=response,
                query_type=query_type,
                response_time_ms=response_time_ms,
                data_sources_used=intent_analysis.get('data_sources', [])
            )
            
            return {
                'query': query,
                'response': response,
                'session_id': session_id,
                'intent_analysis': intent_analysis,
                'response_time_ms': response_time_ms,
                'context_used': len(session_context) > 0,
                'cached': False
            }
            
        except Exception as e:
            error_response = f"I encountered an error: {str(e)}. Let me help you with something else."
            return {
                'query': query,
                'response': error_response,
                'session_id': session_id,
                'error': str(e)
            }
    
    def _analyze_query_intent(self, query: str, session_context: List[Dict], context: Dict = None) -> Dict[str, Any]:
        """Analyze user query intent with conversation context"""
        query_lower = query.lower()
        
        # Check for person-related queries
        if any(keyword in query_lower for keyword in ['haseeb', 'is there', 'status of', 'employee', 'staff member']):
            return {
                'category': 'person_search',
                'confidence': 0.9,
                'data_sources': ['tblstaff', 'tbltasks', 'tblprojects']
            }
        
        # Check for database analytics queries
        if any(keyword in query_lower for keyword in ['how many', 'total', 'count', 'database', 'tables', 'analytics']):
            return {
                'category': 'database_analytics', 
                'confidence': 0.9,
                'data_sources': ['database_statistics']
            }
        
        # Check for task management queries
        if any(keyword in query_lower for keyword in ['task', 'assign', 'deadline', 'project status', 'workload']):
            return {
                'category': 'task_management',
                'confidence': 0.8,
                'data_sources': ['tbltasks', 'tblprojects', 'tbltask_assigned']
            }
        
        # Check for business intelligence queries
        if any(keyword in query_lower for keyword in ['revenue', 'invoice', 'client', 'performance', 'report']):
            return {
                'category': 'business_intelligence',
                'confidence': 0.8,
                'data_sources': ['tblinvoices', 'tblclients', 'tblsales_activity']
            }
        
        return {
            'category': 'general_chat',
            'confidence': 0.6,
            'data_sources': ['conversation_context']
        }
    
    def _handle_task_management_query(self, query: str, context: Dict = None) -> str:
        """Handle task management related queries"""
        try:
            query_lower = query.lower()
            
            if 'overdue' in query_lower or 'late' in query_lower:
                # Find overdue tasks
                overdue_tasks = db.session.execute(text("""
                    SELECT t.name, t.duedate, s.firstname, s.lastname 
                    FROM tbltasks t
                    LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
                    LEFT JOIN tblstaff s ON ta.staffid = s.staffid
                    WHERE t.duedate < NOW() AND t.status != 4
                    ORDER BY t.duedate ASC
                    LIMIT 10
                """)).fetchall()
                
                if overdue_tasks:
                    response = "⏰ **Overdue Tasks Found:**\n\n"
                    for task in overdue_tasks:
                        assignee = f"{task[2]} {task[3]}" if task[2] else "Unassigned"
                        response += f"🔴 {task[0]} - Due: {task[1]} - Assigned to: {assignee}\n"
                    return response
                else:
                    return "✅ **Great news!** No overdue tasks found."
            
            elif 'workload' in query_lower:
                # Show workload distribution
                workload = db.session.execute(text("""
                    SELECT s.firstname, s.lastname, COUNT(ta.taskid) as task_count
                    FROM tblstaff s
                    LEFT JOIN tbltask_assigned ta ON s.staffid = ta.staffid
                    LEFT JOIN tbltasks t ON ta.taskid = t.id
                    WHERE t.status IN (1, 2, 3) OR t.status IS NULL
                    GROUP BY s.staffid
                    ORDER BY task_count DESC
                    LIMIT 10
                """)).fetchall()
                
                response = "📊 **Current Workload Distribution:**\n\n"
                for staff in workload:
                    response += f"👤 {staff[0]} {staff[1]}: {staff[2]} active tasks\n"
                return response
            
            return "I can help you with task management. Try asking about overdue tasks, workload distribution, or specific task assignments."
            
        except Exception as e:
            return f"I encountered an error while analyzing tasks: {str(e)}"
    
    def _handle_business_intelligence_query(self, query: str) -> str:
        """Handle business intelligence and reporting queries"""
        try:
            query_lower = query.lower()
            
            if 'revenue' in query_lower or 'sales' in query_lower:
                # Get sales/revenue information
                revenue_data = db.session.execute(text("""
                    SELECT SUM(total) as total_revenue, COUNT(*) as invoice_count
                    FROM tblinvoices 
                    WHERE status = 2 AND YEAR(datecreated) = YEAR(NOW())
                """)).fetchone()
                
                if revenue_data:
                    return f"💰 **This Year's Performance:**\n\n📈 Total Revenue: ${revenue_data[0] or 0:,.2f}\n📄 Paid Invoices: {revenue_data[1] or 0}"
            
            elif 'client' in query_lower and 'top' in query_lower:
                # Get top clients
                top_clients = db.session.execute(text("""
                    SELECT c.company, COUNT(i.id) as invoice_count, SUM(i.total) as total_spent
                    FROM tblclients c
                    LEFT JOIN tblinvoices i ON c.userid = i.clientid
                    WHERE i.status = 2
                    GROUP BY c.userid
                    ORDER BY total_spent DESC
                    LIMIT 5
                """)).fetchall()
                
                response = "🏆 **Top Clients by Revenue:**\n\n"
                for client in top_clients:
                    response += f"🏢 {client[0]}: ${client[2] or 0:,.2f} ({client[1]} invoices)\n"
                return response
            
            return "I can provide business intelligence on revenue, sales, top clients, and performance metrics. What specific data would you like to see?"
            
        except Exception as e:
            return f"I encountered an error while analyzing business data: {str(e)}"
    
    def _handle_general_query(self, query: str, session_context: List[Dict]) -> str:
        """Handle general queries with conversation context"""
        try:
            context_summary = ""
            if session_context:
                recent_topics = [conv['query_type'] for conv in session_context[:3]]
                context_summary = f"Based on our recent conversation about {', '.join(set(recent_topics))}, "
            
            return f"{context_summary}I'm your AI Coordination Agent. I can help you with:\n\n📊 Database analytics and statistics\n👥 Employee and staff information\n📋 Task management and tracking\n💰 Business intelligence and reports\n🔍 Specific person or project searches\n\nWhat would you like to know?"
            
        except Exception as e:
            return "I'm here to help! Ask me about your business data, staff, tasks, or any analytics you need."
    
    def _handle_person_query(self, query: str) -> str:
        """Handle person-specific queries like 'is Haseeb there'"""
        try:
            query_lower = query.lower()
            
            # Extract person name from query
            person_name = None
            if 'haseeb' in query_lower:
                person_name = 'haseeb'
            else:
                # Try to extract other names (basic implementation)
                words = query_lower.split()
                for word in words:
                    if len(word) > 2 and word.isalpha():
                        # Check if this might be a name in the database
                        name_check = db.session.execute(text("""
                            SELECT firstname, lastname FROM tblstaff 
                            WHERE LOWER(firstname) LIKE %s OR LOWER(lastname) LIKE %s
                            LIMIT 1
                        """), [f'%{word}%', f'%{word}%']).fetchone()
                        if name_check:
                            person_name = word
                            break
            
            if person_name:
                # Search for the person in staff table
                staff_info = db.session.execute(text("""
                    SELECT s.staffid, s.firstname, s.lastname, s.email, s.job_position, s.workplace
                    FROM tblstaff s 
                    WHERE LOWER(s.firstname) LIKE %s OR LOWER(s.lastname) LIKE %s
                """), [f'%{person_name}%', f'%{person_name}%']).fetchall()
                
                if staff_info:
                    response = "👤 **Staff Member Found:**\n\n"
                    for staff in staff_info:
                        response += f"**{staff[1]} {staff[2]}**\n"
                        response += f"📧 Email: {staff[3] or 'Not available'}\n"
                        response += f"💼 Position: {staff[4] or 'Not specified'}\n"
                        response += f"🏢 Workplace: {staff[5] or 'Not specified'}\n\n"
                        
                        # Get their tasks
                        tasks = db.session.execute(text("""
                            SELECT t.name, t.status, t.duedate
                            FROM tbltasks t
                            JOIN tbltask_assigned ta ON t.id = ta.taskid
                            WHERE ta.staffid = %s
                            ORDER BY t.duedate DESC
                            LIMIT 5
                        """), [staff[0]]).fetchall()
                        
                        if tasks:
                            response += "📋 **Recent Tasks:**\n"
                            for task in tasks:
                                status_emoji = "✅" if task[1] == 4 else "🔄" if task[1] in [2, 3] else "📝"
                                response += f"{status_emoji} {task[0]} - Due: {task[2] or 'No due date'}\n"
                        
                        response += "\n"
                    
                    return response
                else:
                    return f"❌ No staff member found with the name '{person_name}'. Try checking the spelling or use a different name."
            else:
                return "🔍 I can help you find staff members. Try asking 'Is [Name] there?' or 'Find [Name]'."
                
        except Exception as e:
            return f"I encountered an error while searching for the person: {str(e)}"