"""
🎯 Enhanced Task Analysis Service
Advanced NLP + Vector Database + Contextual AI Analysis
"""

import openai
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import mysql.connector
from dotenv import load_dotenv

from .nlp_intent_detector import NLPIntentDetector, TaskIntent
from .vector_database_service_simple import TaskVectorDatabase

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.status_mapper import TaskStatusMapper

load_dotenv()

class EnhancedTaskAnalysisService:
    """🚀 Advanced task analysis with NLP intent detection and vector-based semantic search"""
    
    def __init__(self):
        self.nlp_detector = NLPIntentDetector()
        self.vector_db = TaskVectorDatabase()
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Database connection config
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': os.getenv('DB_PASSWORD', '3@6*t:lU'),
            'database': 'u906714182_sqlrrefdvdv'
        }
        
        print("🚀 Enhanced Task Analysis Service initialized with NLP + Vector DB + AI")

    def analyze_query(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """🎯 Main analysis method - processes query through full NLP + Vector + AI pipeline"""
        try:
            print(f"\n🎯 ENHANCED ANALYSIS STARTING for: '{query}'")
            
            # Step 1: NLP Intent Detection and Entity Extraction
            intent_result = self.nlp_detector.detect_intent_and_entities(query)
            intent = intent_result.get('intent', 'general_query')
            employee_name = intent_result.get('employee_name')
            confidence = intent_result.get('confidence', 0.5)
            
            print(f"🧠 NLP Analysis: Intent={intent}, Employee={employee_name}, Confidence={confidence}")
            
            # Step 2: Get task filters and context
            filters = self.nlp_detector.extract_task_filters(query)
            print(f"🔍 Extracted filters: {filters}")
            
            # Step 3: Ensure employee tasks are indexed in vector database
            if employee_name:
                self._ensure_employee_indexed(employee_name)
            
            # Step 4: Route to appropriate handler based on intent
            result = self._route_by_intent(intent, query, employee_name, filters, session_id)
            
            # Add metadata
            result.update({
                'nlp_intent': intent,
                'employee_detected': employee_name,
                'intent_confidence': confidence,
                'filters_applied': filters,
                'processing_pipeline': 'enhanced_nlp_vector_ai',
                'session_id': session_id
            })
            
            print(f"✅ Enhanced analysis completed successfully")
            return result
            
        except Exception as e:
            print(f"❌ Error in enhanced analysis: {e}")
            return self._fallback_response(query, str(e))

    def _ensure_employee_indexed(self, employee_name: str) -> bool:
        """📚 Ensure employee's tasks are indexed in vector database"""
        try:
            # Check if employee has recent embeddings
            stats = self.vector_db.get_collection_stats()
            employee_counts = stats.get('employee_counts', {})
            
            if employee_name not in employee_counts or employee_counts[employee_name] < 5:
                print(f"🔄 Indexing tasks for {employee_name}...")
                index_result = self.vector_db.index_employee_tasks(employee_name)
                return index_result.get('success', False)
            else:
                print(f"✅ {employee_name} already has {employee_counts[employee_name]} tasks indexed")
                return True
                
        except Exception as e:
            print(f"⚠️ Error ensuring indexing: {e}")
            return False

    def _route_by_intent(self, intent: str, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """🎯 Route query to appropriate handler based on detected intent"""
        
        if intent == TaskIntent.LIST_TASKS.value:
            return self._handle_list_tasks(query, employee_name, filters, session_id)
        elif intent == TaskIntent.TASK_SUMMARY.value:
            return self._handle_task_summary(query, employee_name, filters, session_id)
        elif intent == TaskIntent.PERFORMANCE_ANALYSIS.value:
            return self._handle_performance_analysis(query, employee_name, filters, session_id)
        elif intent == TaskIntent.PROGRESS_REPORT.value:
            return self._handle_progress_report(query, employee_name, filters, session_id)
        elif intent == TaskIntent.TASK_COUNT.value:
            return self._handle_task_count(query, employee_name, filters, session_id)
        elif intent == TaskIntent.RECENT_TASKS.value:
            return self._handle_recent_tasks(query, employee_name, filters, session_id)
        elif intent == TaskIntent.OVERDUE_TASKS.value:
            return self._handle_overdue_tasks(query, employee_name, filters, session_id)
        elif intent == TaskIntent.COMPLETED_TASKS.value:
            return self._handle_completed_tasks(query, employee_name, filters, session_id)
        elif intent == TaskIntent.INPROGRESS_TASKS.value:
            return self._handle_inprogress_tasks(query, employee_name, filters, session_id)
        elif intent == TaskIntent.TASK_DETAILS.value:
            return self._handle_task_details(query, employee_name, filters, session_id)
        elif intent == TaskIntent.SPECIFIC_TASK.value:
            return self._handle_specific_task(query, employee_name, filters, session_id)
        else:
            return self._handle_general_query(query, employee_name, filters, session_id)

    def _handle_list_tasks(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """📋 Handle LIST_TASKS intent - return direct task list from MySQL"""
        try:
            print(f"📋 Processing LIST_TASKS for {employee_name}")
            
            # Get tasks directly from MySQL (no summarization)
            tasks = self._get_filtered_tasks(employee_name, filters)
            
            if not tasks:
                return {
                    'success': True,
                    'analysis': f"No tasks found for {employee_name or 'the specified criteria'}.",
                    'task_count': 0,
                    'intent_type': 'list_tasks',
                    'direct_list': True
                }
            
            # Format as direct list
            analysis = f"Tasks for {employee_name}:\n\n"
            for i, task in enumerate(tasks, 1):
                status_emoji = self._get_status_emoji(task.get('status', ''))
                analysis += f"{i}. {status_emoji} {task['name']}\n"
                if task.get('dateadded'):
                    analysis += f"   📅 Created: {task['dateadded']}\n"
                # Fix priority check to handle different data types
                priority = task.get('priority')
                if priority is not None:
                    try:
                        priority_num = int(priority)
                        if priority_num > 2:
                            analysis += f"   🔴 High Priority\n"
                    except (ValueError, TypeError):
                        pass  # Skip if priority is not a valid number
                analysis += "\n"
            
            analysis += f"**Total: {len(tasks)} tasks**"
            
            return {
                'success': True,
                'analysis': analysis,
                'raw_data': tasks,
                'task_count': len(tasks),
                'intent_type': 'list_tasks',
                'direct_list': True,
                'employee': employee_name
            }
            
        except Exception as e:
            print(f"❌ Error in list_tasks handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_task_summary(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """📊 Handle TASK_SUMMARY intent - provide AI-generated summary using vector context"""
        try:
            print(f"📊 Processing TASK_SUMMARY for {employee_name}")
            
            # Get relevant tasks using semantic search
            relevant_tasks = self.vector_db.get_contextual_tasks(
                query, employee_name, 'task_summary', top_k=12
            )
            
            if not relevant_tasks:
                return {
                    'success': True,
                    'analysis': f"No tasks found to summarize for {employee_name}.",
                    'intent_type': 'task_summary'
                }
            
            # Generate AI summary with context
            summary = self._generate_ai_summary(query, relevant_tasks, employee_name, 'summary')
            
            return {
                'success': True,
                'analysis': summary,
                'context_tasks': len(relevant_tasks),
                'intent_type': 'task_summary',
                'employee': employee_name,
                'ai_generated': True
            }
            
        except Exception as e:
            print(f"❌ Error in task_summary handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_performance_analysis(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """📈 Handle PERFORMANCE_ANALYSIS intent - detailed performance metrics and insights"""
        try:
            print(f"📈 Processing PERFORMANCE_ANALYSIS for {employee_name}")
            
            # Get performance-related tasks
            relevant_tasks = self.vector_db.get_contextual_tasks(
                query, employee_name, 'performance', top_k=15
            )
            
            # Get additional performance metrics
            performance_metrics = self._calculate_performance_metrics(employee_name, filters)
            
            # Generate AI-powered performance analysis
            analysis = self._generate_ai_summary(
                query, relevant_tasks, employee_name, 'performance', performance_metrics
            )
            
            return {
                'success': True,
                'analysis': analysis,
                'performance_metrics': performance_metrics,
                'context_tasks': len(relevant_tasks),
                'intent_type': 'performance_analysis',
                'employee': employee_name,
                'ai_generated': True
            }
            
        except Exception as e:
            print(f"❌ Error in performance_analysis handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_progress_report(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """📊 Handle PROGRESS_REPORT intent - current status and progress updates"""
        try:
            print(f"📊 Processing PROGRESS_REPORT for {employee_name}")
            
            # Get recent and in-progress tasks
            relevant_tasks = self.vector_db.get_contextual_tasks(
                f"{query} progress status recent updates", employee_name, 'progress_report', top_k=10
            )
            
            # Calculate progress metrics
            progress_data = self._calculate_progress_metrics(employee_name)
            
            # Generate progress report
            report = self._generate_ai_summary(
                query, relevant_tasks, employee_name, 'progress', progress_data
            )
            
            return {
                'success': True,
                'analysis': report,
                'progress_data': progress_data,
                'context_tasks': len(relevant_tasks),
                'intent_type': 'progress_report',
                'employee': employee_name,
                'ai_generated': True
            }
            
        except Exception as e:
            print(f"❌ Error in progress_report handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_recent_tasks(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """🕒 Handle RECENT_TASKS intent - show latest tasks"""
        try:
            print(f"🕒 Processing RECENT_TASKS for {employee_name}")
            
            # Add time filter for recent tasks
            filters = filters.copy()
            filters['time_period'] = 'recent'
            
            # Get recent tasks
            tasks = self._get_filtered_tasks(employee_name, filters, limit=15)
            
            if not tasks:
                return {
                    'success': True,
                    'analysis': f"No recent tasks found for {employee_name}.",
                    'intent_type': 'recent_tasks'
                }
            
            # Format recent tasks with timestamps
            analysis = f"Recent tasks for {employee_name}:\n\n"
            for i, task in enumerate(tasks[:10], 1):
                status_emoji = self._get_status_emoji(task.get('status', ''))
                date_str = self._format_relative_date(task.get('dateadded'))
                analysis += f"{i}. {status_emoji} {task['name']}\n"
                analysis += f"   📅 {date_str}\n\n"
            
            if len(tasks) > 10:
                analysis += f"... and {len(tasks) - 10} more recent tasks\n\n"
            
            analysis += f"**Total recent tasks: {len(tasks)}**"
            
            return {
                'success': True,
                'analysis': analysis,
                'raw_data': tasks,
                'task_count': len(tasks),
                'intent_type': 'recent_tasks',
                'employee': employee_name
            }
            
        except Exception as e:
            print(f"❌ Error in recent_tasks handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_overdue_tasks(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """🚨 Handle OVERDUE_TASKS intent - show overdue tasks using direct CRM query"""
        try:
            print(f"🚨 Processing OVERDUE_TASKS for {employee_name}")
            
            if not employee_name:
                return {
                    'success': False,
                    'analysis': "Please specify an employee name to check overdue tasks.",
                    'intent_type': 'overdue_tasks'
                }
            
            # Check if user wants full/complete list
            query_lower = query.lower()
            show_full_list = any(keyword in query_lower for keyword in [
                'full list', 'complete list', 'all overdue', 'every overdue', 
                'entire list', 'show all', 'list all', 'full overdue'
            ])
            
            # Use our new API to get overdue tasks
            import requests
            base_url = "http://127.0.0.1:5001"
            
            try:
                response = requests.get(f"{base_url}/api/employee/{employee_name}/overdue-tasks")
                data = response.json()
                
                if not data.get('success'):
                    return {
                        'success': True,
                        'analysis': f"❌ Could not retrieve overdue tasks for {employee_name}: {data.get('error', 'Unknown error')}",
                        'intent_type': 'overdue_tasks',
                        'employee': employee_name
                    }
                
                overdue_tasks = data.get('overdue_tasks', [])
                stats = data.get('stats', {})
                analysis_data = data.get('analysis', {})
                
                if not overdue_tasks:
                    analysis = f"✅ **Excellent News!** {employee_name} has **NO overdue tasks**!\n\n"
                    analysis += f"📊 **Task Summary:**\n"
                    analysis += f"• Total Tasks: {stats.get('total_tasks', 0)}\n"
                    analysis += f"• Completed: {stats.get('completed_count', 0)}\n"
                    analysis += f"• Upcoming: {stats.get('upcoming_count', 0)}\n\n"
                    analysis += f"🎯 **Status:** All tasks are either completed or within their deadlines."
                    
                    return {
                        'success': True,
                        'analysis': analysis,
                        'overdue_tasks': [],
                        'stats': stats,
                        'intent_type': 'overdue_tasks',
                        'employee': employee_name
                    }
                
                # Format overdue tasks analysis
                analysis = f"🚨 **OVERDUE TASKS ALERT for {employee_name}**\n\n"
                analysis += f"📊 **Summary:**\n"
                analysis += f"• **{len(overdue_tasks)} overdue tasks** out of {stats.get('total_tasks', 0)} total\n"
                analysis += f"• Completion Rate: {stats.get('completed_count', 0)}/{stats.get('total_tasks', 0)} ({round((stats.get('completed_count', 0) / max(stats.get('total_tasks', 1), 1)) * 100, 1)}%)\n\n"
                
                # Show overdue tasks - more if full list requested
                max_tasks_to_show = len(overdue_tasks) if show_full_list else min(15, len(overdue_tasks))
                list_title = "🔴 **Complete Overdue Tasks List:**" if show_full_list else "🔴 **Most Critical Overdue Tasks:**"
                
                analysis += f"{list_title}\n"
                for i, task in enumerate(overdue_tasks[:max_tasks_to_show], 1):
                    days_overdue = task.get('days_overdue', 0)
                    urgency_emoji = "🔥" if days_overdue > 30 else "⚠️" if days_overdue > 7 else "📅"
                    
                    analysis += f"{i}. {urgency_emoji} **{task.get('task_name', 'Unnamed Task')}**\n"
                    analysis += f"   📅 Due: {task.get('duedate', 'Unknown')} ({days_overdue} days overdue)\n"
                    analysis += f"   📊 Status: {task.get('status_name', 'Unknown')}\n"
                    analysis += f"   ⚡ Priority: {task.get('priority_name', 'Unknown')}\n"
                    
                    if task.get('project_name'):
                        analysis += f"   🚀 Project: {task['project_name']}\n"
                    analysis += "\n"
                
                if not show_full_list and len(overdue_tasks) > max_tasks_to_show:
                    analysis += f"... and **{len(overdue_tasks) - max_tasks_to_show} more** overdue tasks\n"
                    analysis += f"💡 *Ask for 'full list of overdue tasks' to see all {len(overdue_tasks)} tasks*\n\n"
                elif show_full_list:
                    analysis += f"📋 **Showing all {len(overdue_tasks)} overdue tasks above**\n\n"
                
                # Priority breakdown
                priority_breakdown = analysis_data.get('priority_breakdown', {})
                if priority_breakdown:
                    analysis += f"📈 **Priority Breakdown:**\n"
                    for priority in ['Urgent', 'High', 'Medium', 'Low']:
                        if priority in priority_breakdown:
                            count = len(priority_breakdown[priority])
                            emoji = "🔴" if priority == "Urgent" else "🟠" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                            analysis += f"• {emoji} {priority}: {count} tasks\n"
                    analysis += "\n"
                
                # Urgency analysis
                urgency = analysis_data.get('urgency_analysis', {})
                if urgency:
                    analysis += f"⚠️ **Urgency Analysis:**\n"
                    if urgency.get('critical_count', 0) > 0:
                        analysis += f"🔴 **Critical** (>30 days): {urgency['critical_count']} tasks - **IMMEDIATE ACTION REQUIRED**\n"
                    if urgency.get('urgent_count', 0) > 0:
                        analysis += f"🟠 **Urgent** (8-30 days): {urgency['urgent_count']} tasks - Address this week\n"
                    if urgency.get('recent_count', 0) > 0:
                        analysis += f"🟡 **Recent** (1-7 days): {urgency['recent_count']} tasks - Schedule completion soon\n"
                
                return {
                    'success': True,
                    'analysis': analysis,
                    'overdue_tasks': overdue_tasks,
                    'stats': stats,
                    'urgency_analysis': urgency,
                    'priority_breakdown': priority_breakdown,
                    'intent_type': 'overdue_tasks',
                    'employee': employee_name,
                    'raw_data': data
                }
                
            except requests.RequestException as e:
                return {
                    'success': True,
                    'analysis': f"❌ Could not connect to overdue tasks API: {str(e)}",
                    'intent_type': 'overdue_tasks',
                    'employee': employee_name
                }
            
        except Exception as e:
            print(f"❌ Error in overdue_tasks handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_completed_tasks(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """✅ Handle COMPLETED_TASKS intent - show completed tasks using direct CRM query"""
        try:
            print(f"✅ Processing COMPLETED_TASKS for {employee_name}")
            
            if not employee_name:
                return {
                    'success': False,
                    'analysis': "Please specify an employee name to check completed tasks.",
                    'intent_type': 'completed_tasks'
                }
            
            # Check if user wants full/complete list
            query_lower = query.lower()
            show_full_list = any(keyword in query_lower for keyword in [
                'full list', 'complete list', 'all completed', 'every completed', 
                'entire list', 'show all', 'list all', 'full completed'
            ])
            
            # Use our new API to get completed tasks
            import requests
            base_url = "http://127.0.0.1:5001"
            
            try:
                response = requests.get(f"{base_url}/api/employee/{employee_name}/completed-tasks")
                data = response.json()
                
                if not data.get('success'):
                    return {
                        'success': True,
                        'analysis': f"❌ Could not retrieve completed tasks for {employee_name}: {data.get('error', 'Unknown error')}",
                        'intent_type': 'completed_tasks',
                        'employee': employee_name
                    }
                
                completed_tasks = data.get('completed_tasks', [])
                stats = data.get('stats', {})
                analysis_data = data.get('analysis', {})
                
                if not completed_tasks:
                    analysis = f"📋 **No Completed Tasks Found** for {employee_name}\n\n"
                    analysis += f"📊 **Task Summary:**\n"
                    analysis += f"• Total Tasks: {stats.get('total_tasks', 0)}\n"
                    analysis += f"• Completed: {stats.get('completed_count', 0)}\n\n"
                    analysis += f"💡 **Note:** {employee_name} may not have completed any tasks yet, or tasks may be marked with different status codes."
                    
                    return {
                        'success': True,
                        'analysis': analysis,
                        'completed_tasks': [],
                        'stats': stats,
                        'intent_type': 'completed_tasks',
                        'employee': employee_name
                    }
                
                # Format completed tasks analysis
                analysis = f"✅ **COMPLETED TASKS for {employee_name}**\n\n"
                analysis += f"📊 **Summary:**\n"
                analysis += f"• **{len(completed_tasks)} completed tasks** out of {stats.get('total_tasks', 0)} total\n"
                analysis += f"• Completion Rate: {stats.get('completion_rate', 0)}%\n\n"
                
                # Show completed tasks
                max_tasks_to_show = len(completed_tasks) if show_full_list else min(15, len(completed_tasks))
                list_title = "✅ **Complete Finished Tasks List:**" if show_full_list else "✅ **Most Recent Completed Tasks:**"
                
                analysis += f"{list_title}\n"
                for i, task in enumerate(completed_tasks[:max_tasks_to_show], 1):
                    completion_emoji = "🏆" if task.get('priority_name') == 'Urgent' else "✅"
                    
                    analysis += f"{i}. {completion_emoji} **{task.get('task_name', 'Unnamed Task')}**\n"
                    analysis += f"   ✅ Completed: {task.get('datefinished', 'Unknown')}\n"
                    analysis += f"   ⚡ Priority: {task.get('priority_name', 'Unknown')}\n"
                    
                    if task.get('project_name'):
                        analysis += f"   🚀 Project: {task['project_name']}\n"
                    if task.get('completion_days') and task['completion_days'] > 0:
                        analysis += f"   ⏱️ Duration: {task['completion_days']} days\n"
                    analysis += "\n"
                
                if not show_full_list and len(completed_tasks) > max_tasks_to_show:
                    analysis += f"... and **{len(completed_tasks) - max_tasks_to_show} more** completed tasks\n"
                    analysis += f"💡 *Ask for 'full list of completed tasks' to see all {len(completed_tasks)} tasks*\n\n"
                elif show_full_list:
                    analysis += f"📋 **Showing all {len(completed_tasks)} completed tasks above**\n\n"
                
                # Priority breakdown
                priority_breakdown = analysis_data.get('priority_breakdown', {})
                if priority_breakdown:
                    analysis += f"📈 **Completed Tasks by Priority:**\n"
                    for priority in ['Urgent', 'High', 'Medium', 'Low']:
                        if priority in priority_breakdown:
                            count = len(priority_breakdown[priority])
                            emoji = "🔴" if priority == "Urgent" else "🟠" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                            analysis += f"• {emoji} {priority}: {count} tasks\n"
                    analysis += "\n"
                
                return {
                    'success': True,
                    'analysis': analysis,
                    'completed_tasks': completed_tasks,
                    'stats': stats,
                    'priority_breakdown': priority_breakdown,
                    'intent_type': 'completed_tasks',
                    'employee': employee_name,
                    'raw_data': data
                }
                
            except requests.RequestException as e:
                return {
                    'success': True,
                    'analysis': f"❌ Could not connect to completed tasks API: {str(e)}",
                    'intent_type': 'completed_tasks',
                    'employee': employee_name
                }
            
        except Exception as e:
            print(f"❌ Error in completed_tasks handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_inprogress_tasks(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """🔄 Handle INPROGRESS_TASKS intent - show in-progress tasks using direct CRM query"""
        try:
            print(f"🔄 Processing INPROGRESS_TASKS for {employee_name}")
            
            if not employee_name:
                return {
                    'success': False,
                    'analysis': "Please specify an employee name to check in-progress tasks.",
                    'intent_type': 'inprogress_tasks'
                }
            
            # Check if user wants full/complete list
            query_lower = query.lower()
            show_full_list = any(keyword in query_lower for keyword in [
                'full list', 'complete list', 'all progress', 'all active', 
                'entire list', 'show all', 'list all', 'full progress'
            ])
            
            # Use our new API to get in-progress tasks
            import requests
            base_url = "http://127.0.0.1:5001"
            
            try:
                response = requests.get(f"{base_url}/api/employee/{employee_name}/inprogress-tasks")
                data = response.json()
                
                if not data.get('success'):
                    return {
                        'success': True,
                        'analysis': f"❌ Could not retrieve in-progress tasks for {employee_name}: {data.get('error', 'Unknown error')}",
                        'intent_type': 'inprogress_tasks',
                        'employee': employee_name
                    }
                
                inprogress_tasks = data.get('inprogress_tasks', [])
                stats = data.get('stats', {})
                analysis_data = data.get('analysis', {})
                
                if not inprogress_tasks:
                    analysis = f"🔄 **No Active Tasks** for {employee_name}\n\n"
                    analysis += f"📊 **Task Summary:**\n"
                    analysis += f"• Total Tasks: {stats.get('total_tasks', 0)}\n"
                    analysis += f"• In Progress: {stats.get('inprogress_count', 0)}\n\n"
                    analysis += f"💡 **Status:** {employee_name} currently has no tasks in progress. All tasks may be completed or not yet started."
                    
                    return {
                        'success': True,
                        'analysis': analysis,
                        'inprogress_tasks': [],
                        'stats': stats,
                        'intent_type': 'inprogress_tasks',
                        'employee': employee_name
                    }
                
                # Format in-progress tasks analysis
                analysis = f"🔄 **IN-PROGRESS TASKS for {employee_name}**\n\n"
                analysis += f"📊 **Summary:**\n"
                analysis += f"• **{len(inprogress_tasks)} active tasks** out of {stats.get('total_tasks', 0)} total\n"
                analysis += f"• Progress Rate: {stats.get('inprogress_rate', 0)}%\n\n"
                
                # Show in-progress tasks
                max_tasks_to_show = len(inprogress_tasks) if show_full_list else min(15, len(inprogress_tasks))
                list_title = "🔄 **Complete Active Tasks List:**" if show_full_list else "🔄 **Current Active Tasks:**"
                
                analysis += f"{list_title}\n"
                for i, task in enumerate(inprogress_tasks[:max_tasks_to_show], 1):
                    status_emoji = "🔄" if task.get('status_name') == 'In Progress' else "🧪" if task.get('status_name') == 'Testing' else "⏳"
                    
                    analysis += f"{i}. {status_emoji} **{task.get('task_name', 'Unnamed Task')}**\n"
                    analysis += f"   📊 Status: {task.get('status_name', 'Unknown')}\n"
                    analysis += f"   ⚡ Priority: {task.get('priority_name', 'Unknown')}\n"
                    
                    if task.get('duedate'):
                        days_until_due = task.get('days_until_due', 0)
                        if days_until_due is not None:
                            if days_until_due < 0:
                                analysis += f"   🚨 Overdue by {abs(days_until_due)} days\n"
                            elif days_until_due == 0:
                                analysis += f"   📅 Due today!\n"
                            else:
                                analysis += f"   📅 Due in {days_until_due} days\n"
                    
                    if task.get('project_name'):
                        analysis += f"   🚀 Project: {task['project_name']}\n"
                    analysis += "\n"
                
                if not show_full_list and len(inprogress_tasks) > max_tasks_to_show:
                    analysis += f"... and **{len(inprogress_tasks) - max_tasks_to_show} more** active tasks\n"
                    analysis += f"💡 *Ask for 'full list of in-progress tasks' to see all {len(inprogress_tasks)} tasks*\n\n"
                elif show_full_list:
                    analysis += f"📋 **Showing all {len(inprogress_tasks)} active tasks above**\n\n"
                
                # Status breakdown
                status_breakdown = analysis_data.get('status_breakdown', {})
                if status_breakdown:
                    analysis += f"📈 **Tasks by Status:**\n"
                    for status in ['In Progress', 'Testing', 'Awaiting Feedback']:
                        if status in status_breakdown:
                            count = len(status_breakdown[status])
                            emoji = "🔄" if status == "In Progress" else "🧪" if status == "Testing" else "⏳"
                            analysis += f"• {emoji} {status}: {count} tasks\n"
                    analysis += "\n"
                
                return {
                    'success': True,
                    'analysis': analysis,
                    'inprogress_tasks': inprogress_tasks,
                    'stats': stats,
                    'status_breakdown': status_breakdown,
                    'intent_type': 'inprogress_tasks',
                    'employee': employee_name,
                    'raw_data': data
                }
                
            except requests.RequestException as e:
                return {
                    'success': True,
                    'analysis': f"❌ Could not connect to in-progress tasks API: {str(e)}",
                    'intent_type': 'inprogress_tasks',
                    'employee': employee_name
                }
            
        except Exception as e:
            print(f"❌ Error in inprogress_tasks handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_task_count(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """🔢 Handle TASK_COUNT intent - provide task counts and statistics"""
        try:
            print(f"🔢 Processing TASK_COUNT for {employee_name}")
            
            # Get all tasks for counting
            all_tasks = self._get_filtered_tasks(employee_name, filters)
            
            # Calculate various counts
            total_count = len(all_tasks)
            status_counts = {}
            priority_counts = {}
            
            for task in all_tasks:
                status = task.get('status', 'Unknown')
                priority = task.get('priority', 0)
                
                status_counts[status] = status_counts.get(status, 0) + 1
                
                if priority >= 3:
                    priority_counts['High'] = priority_counts.get('High', 0) + 1
                elif priority == 2:
                    priority_counts['Medium'] = priority_counts.get('Medium', 0) + 1
                else:
                    priority_counts['Low'] = priority_counts.get('Low', 0) + 1
            
            # Format response
            analysis = f"Task statistics for {employee_name}:\n\n"
            analysis += f"📊 **Total Tasks: {total_count}**\n\n"
            
            if status_counts:
                analysis += "📋 **By Status:**\n"
                for status, count in status_counts.items():
                    emoji = self._get_status_emoji(status)
                    analysis += f"• {emoji} {status}: {count}\n"
                analysis += "\n"
            
            if priority_counts:
                analysis += "🎯 **By Priority:**\n"
                for priority, count in priority_counts.items():
                    emoji = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                    analysis += f"• {emoji} {priority}: {count}\n"
            
            return {
                'success': True,
                'analysis': analysis,
                'total_count': total_count,
                'status_counts': status_counts,
                'priority_counts': priority_counts,
                'intent_type': 'task_count',
                'employee': employee_name
            }
            
        except Exception as e:
            print(f"❌ Error in task_count handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_task_details(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """🔍 Handle TASK_DETAILS intent - detailed information about specific tasks"""
        try:
            print(f"🔍 Processing TASK_DETAILS for {employee_name}")
            
            # Use semantic search to find most relevant tasks
            relevant_tasks = self.vector_db.semantic_search(query, employee_name, top_k=5)
            
            if not relevant_tasks:
                return {
                    'success': True,
                    'analysis': f"No matching tasks found for: {query}",
                    'intent_type': 'task_details'
                }
            
            # Generate detailed analysis
            analysis = self._generate_ai_summary(query, relevant_tasks, employee_name, 'details')
            
            return {
                'success': True,
                'analysis': analysis,
                'relevant_tasks': relevant_tasks,
                'intent_type': 'task_details',
                'employee': employee_name,
                'ai_generated': True
            }
            
        except Exception as e:
            print(f"❌ Error in task_details handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_specific_task(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """🎯 Handle SPECIFIC_TASK intent - information about one particular task"""
        try:
            print(f"🎯 Processing SPECIFIC_TASK query")
            
            # Use semantic search to find the most relevant task
            relevant_tasks = self.vector_db.semantic_search(query, employee_name, top_k=3)
            
            if not relevant_tasks:
                return {
                    'success': True,
                    'analysis': f"No specific task found matching: {query}",
                    'intent_type': 'specific_task'
                }
            
            # Focus on the most relevant task
            top_task = relevant_tasks[0]
            
            analysis = f"**Task Details:**\n\n"
            analysis += f"📋 **Name:** {top_task['task_name']}\n"
            analysis += f"👤 **Employee:** {top_task['employee_name']}\n"
            analysis += f"📊 **Status:** {top_task['status']}\n"
            
            if top_task['priority']:
                analysis += f"🎯 **Priority:** {top_task['priority']}\n"
            if top_task['dateadded']:
                analysis += f"📅 **Created:** {top_task['dateadded']}\n"
            
            analysis += f"\n🔍 **Relevance Score:** {top_task['similarity_score']:.2f}\n"
            analysis += f"\n📝 **Context:** {top_task['document'][:200]}..."
            
            return {
                'success': True,
                'analysis': analysis,
                'task_details': top_task,
                'intent_type': 'specific_task',
                'similarity_score': top_task['similarity_score']
            }
            
        except Exception as e:
            print(f"❌ Error in specific_task handler: {e}")
            return self._fallback_response(query, str(e))

    def _handle_general_query(self, query: str, employee_name: str, filters: Dict, session_id: str) -> Dict[str, Any]:
        """❓ Handle GENERAL_QUERY intent - flexible AI-powered response"""
        try:
            print(f"❓ Processing GENERAL_QUERY")
            
            # Use semantic search for context
            relevant_tasks = []
            if employee_name:
                relevant_tasks = self.vector_db.semantic_search(query, employee_name, top_k=8)
            
            # Generate contextual AI response
            analysis = self._generate_ai_summary(query, relevant_tasks, employee_name, 'general')
            
            return {
                'success': True,
                'analysis': analysis,
                'context_tasks': len(relevant_tasks),
                'intent_type': 'general_query',
                'employee': employee_name,
                'ai_generated': True
            }
            
        except Exception as e:
            print(f"❌ Error in general_query handler: {e}")
            return self._fallback_response(query, str(e))

    # Helper methods...
    def _get_filtered_tasks(self, employee_name: str, filters: Dict, limit: int = 50) -> List[Dict]:
        """📊 Get tasks from MySQL with applied filters"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Build SQL query with filters
            sql = """
            SELECT 
                t.id, t.name, t.status, t.priority, t.dateadded, t.duedate,
                s.firstname, s.lastname
            FROM tbltasks t
            LEFT JOIN tblstaff s ON t.addedfrom = s.staffid
            WHERE 1=1
            """
            params = []
            
            # Employee filter
            if employee_name:
                sql += " AND (s.firstname LIKE %s OR s.lastname LIKE %s)"
                params.extend([f"%{employee_name}%", f"%{employee_name}%"])
            
            # Time filters
            time_period = filters.get('time_period')
            if time_period == 'today':
                sql += " AND DATE(t.dateadded) = CURDATE()"
            elif time_period == 'week':
                sql += " AND t.dateadded >= DATE_SUB(NOW(), INTERVAL 1 WEEK)"
            elif time_period == 'month':
                sql += " AND t.dateadded >= DATE_SUB(NOW(), INTERVAL 1 MONTH)"
            elif time_period == 'recent':
                sql += " AND t.dateadded >= DATE_SUB(NOW(), INTERVAL 2 WEEK)"
            
            # Status filter
            if filters.get('status'):
                status_map = {
                    'completed': ['Completed', 'Done', 'Finished'],
                    'pending': ['Pending', 'Not Started', 'Waiting'],
                    'in_progress': ['In Progress', 'Active', 'Working']
                }
                statuses = status_map.get(filters['status'], [filters['status']])
                placeholders = ','.join(['%s'] * len(statuses))
                sql += f" AND t.status IN ({placeholders})"
                params.extend(statuses)
            
            # Priority filter
            if filters.get('priority'):
                priority_map = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
                min_priority = priority_map.get(filters['priority'], 1)
                sql += " AND t.priority >= %s"
                params.append(min_priority)
            
            sql += " ORDER BY t.dateadded DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(sql, params)
            tasks = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return tasks
            
        except Exception as e:
            print(f"❌ Error getting filtered tasks: {e}")
            return []

    def _generate_ai_summary(self, query: str, relevant_tasks: List[Dict], employee_name: str, 
                           summary_type: str, additional_data: Dict = None) -> str:
        """🤖 Generate AI-powered summary using task context with human-readable status names"""
        try:
            # Prepare context from relevant tasks with human-readable status/priority
            context_parts = []
            for task in relevant_tasks[:8]:  # Limit context size
                # Get human-readable status and priority
                status_info = TaskStatusMapper.get_status_info(task.get('status', 0))
                priority_info = TaskStatusMapper.get_priority_info(task.get('priority', 3))
                
                context_parts.append(
                    f"Task: {task.get('task_name', task.get('name', 'Unnamed Task'))} | "
                    f"Status: {status_info['name']} {status_info['emoji']} | "
                    f"Priority: {priority_info['name']} {priority_info['emoji']} | "
                    f"Created: {task.get('dateadded', 'Unknown')}"
                )
            
            context = "\n".join(context_parts)
            
            # Create specialized prompts based on summary type
            if summary_type == 'performance':
                # Format status distribution for better readability
                status_summary = ""
                if additional_data and 'status_distribution_detailed' in additional_data:
                    status_items = []
                    for item in additional_data['status_distribution_detailed']:
                        status_items.append(f"{item['count']} {item['status_name']} {item['emoji']}")
                    status_summary = f"Status Distribution: {', '.join(status_items)}"
                
                prompt = f"""
                Based on the following task data for {employee_name}, provide a performance analysis:
                
                TASK CONTEXT:
                {context}
                
                PERFORMANCE METRICS:
                {status_summary}
                Total Tasks: {additional_data.get('total_tasks', 'Unknown') if additional_data else 'Unknown'}
                Active Tasks: {additional_data.get('active_tasks', 'Unknown') if additional_data else 'Unknown'}
                Recent Completed: {additional_data.get('recent_completed', 'Unknown') if additional_data else 'Unknown'}
                
                USER QUERY: "{query}"
                
                Provide a comprehensive performance analysis including:
                - Task completion patterns
                - Work quality indicators  
                - Productivity insights
                - Areas of strength and improvement
                - Explain what each status means in practical terms
                
                Keep response under 300 words and focus on actionable insights.
                """
            elif summary_type == 'summary':
                prompt = f"""
                Provide a concise summary of {employee_name}'s tasks based on this context:
                
                TASK CONTEXT:
                {context}
                
                USER QUERY: "{query}"
                
                Create a brief overview highlighting:
                - Main work areas/projects
                - Current focus
                - Key accomplishments
                - Overall workload
                
                Keep response under 200 words.
                """
            elif summary_type == 'progress':
                prompt = f"""
                Create a progress report for {employee_name} based on this task data:
                
                TASK CONTEXT:
                {context}
                
                PROGRESS DATA:
                {json.dumps(additional_data, indent=2) if additional_data else 'None available'}
                
                USER QUERY: "{query}"
                
                Include:
                - Current status of active tasks
                - Recent completions
                - Upcoming deadlines
                - Progress trends
                
                Keep response under 250 words.
                """
            else:
                prompt = f"""
                Answer this query about {employee_name}'s tasks using the provided context:
                
                TASK CONTEXT:
                {context}
                
                USER QUERY: "{query}"
                
                Provide a helpful, contextual response based on the available task data.
                Keep response concise and relevant.
                """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating AI summary: {e}")
            return f"Analysis for {employee_name}: Found {len(relevant_tasks)} relevant tasks. Unable to generate detailed summary at this time."

    def _calculate_performance_metrics(self, employee_name: str, filters: Dict) -> Dict:
        """📊 Calculate performance metrics for an employee"""
        try:
            tasks = self._get_filtered_tasks(employee_name, {}, limit=100)
            
            total_tasks = len(tasks)
            
            # Fix status handling
            completed_tasks = 0
            high_priority_tasks = 0
            
            for task in tasks:
                # Handle status safely
                status = task.get('status', '')
                if status and str(status).lower() in ['completed', 'done', 'finished']:
                    completed_tasks += 1
                
                # Handle priority safely
                priority = task.get('priority', 0)
                try:
                    if int(priority) >= 3:
                        high_priority_tasks += 1
                except (ValueError, TypeError):
                    pass
            
            # Calculate completion rate
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Recent activity (last 30 days)
            recent_tasks = self._get_filtered_tasks(employee_name, {'time_period': 'month'})
            recent_activity = len(recent_tasks)
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': round(completion_rate, 1),
                'high_priority_tasks': high_priority_tasks,
                'recent_activity_30d': recent_activity,
                'average_tasks_per_week': round(recent_activity / 4.3, 1) if recent_activity > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error calculating performance metrics: {e}")
            return {}

    def _calculate_progress_metrics(self, employee_name: str) -> Dict:
        """📈 Calculate progress-related metrics with human-readable status names"""
        try:
            all_tasks = self._get_filtered_tasks(employee_name, {}, limit=100)
            recent_tasks = self._get_filtered_tasks(employee_name, {'time_period': 'week'})
            
            # Status distribution with human-readable names
            status_counts = {}
            status_codes = {}  # Keep track of raw status codes
            for task in all_tasks:
                status_code = task.get('status', 0)
                status_info = TaskStatusMapper.get_status_info(status_code)
                status_name = status_info['name']
                
                status_counts[status_name] = status_counts.get(status_name, 0) + 1
                status_codes[status_code] = status_codes.get(status_code, 0) + 1
            
            # Recent completions - check for completed status (status 5)
            recent_completed = 0
            for task in recent_tasks:
                status_code = task.get('status', 0)
                if status_code == 5:  # Status 5 is completed
                    recent_completed += 1
            
            # Calculate active tasks (non-completed statuses)
            active_tasks = 0
            for task in all_tasks:
                status_code = task.get('status', 0)
                if status_code != 5:  # Not completed
                    active_tasks += 1
            
            # Format status distribution for display
            formatted_status = TaskStatusMapper.format_status_distribution(
                [(code, count) for code, count in status_codes.items()]
            )
            
            return {
                'total_tasks': len(all_tasks),
                'recent_week_tasks': len(recent_tasks),
                'recent_completed': recent_completed,
                'status_distribution': status_counts,
                'status_distribution_detailed': formatted_status,
                'active_tasks': active_tasks
            }
            
        except Exception as e:
            print(f"❌ Error calculating progress metrics: {e}")
            return {}

    def _get_status_emoji(self, status) -> str:
        """📊 Get emoji for task status"""
        status_emojis = {
            'completed': '✅',
            'done': '✅',
            'finished': '✅',
            'in progress': '🔄',
            'active': '🔄',
            'working': '🔄',
            'pending': '⏳',
            'waiting': '⏳',
            'not started': '⏳',
            'overdue': '🚨',
            'cancelled': '❌',
            'on hold': '⏸️'
        }
        # Ensure status is a string before calling .lower()
        if status is None:
            return '📋'
        status_str = str(status).lower()
        return status_emojis.get(status_str, '📋')

    def _format_relative_date(self, date_obj) -> str:
        """📅 Format date as relative time"""
        if not date_obj:
            return "Unknown date"
        
        try:
            if isinstance(date_obj, str):
                # Handle string dates
                return f"Created {date_obj}"
            
            now = datetime.now()
            if hasattr(date_obj, 'date'):
                date_obj = date_obj.date()
                now = now.date()
            
            diff = now - date_obj
            
            if diff.days == 0:
                return "Today"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = diff.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
                
        except Exception:
            return str(date_obj)

    def _fallback_response(self, query: str, error: str) -> Dict[str, Any]:
        """🔄 Fallback response when processing fails"""
        return {
            'success': False,
            'analysis': f"I encountered an issue processing your query: '{query}'. Please try rephrasing your question.",
            'error': error,
            'intent_type': 'fallback',
            'ai_generated': False
        }