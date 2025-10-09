"""
AI-Powered Employee Performance Analyst Service

This service uses OpenAI's NLP capabilities to intelligently understand human queries
about employee performance and provide detailed insights and recommendations.
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import openai
from dataclasses import dataclass

@dataclass
class EmployeePerformance:
    """Data structure for employee performance metrics"""
    employee_name: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    completion_rate: float
    avg_task_duration: Optional[float]
    recent_activity: List[Dict]
    performance_trend: str

@dataclass
class QueryAnalysis:
    """Result of OpenAI query analysis"""
    is_employee_query: bool
    employee_name: Optional[str]
    intent: str
    confidence: float
    query_type: str
    additional_context: Dict[str, Any]

class EmployeeAnalystService:
    """AI-powered employee performance analyst using OpenAI NLP"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        else:
            print("Warning: OPENAI_API_KEY not found in environment")
        
        # In-memory cache for employee performance data
        self.employee_cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # 5 minutes
    
    def analyze_query_with_ai(self, user_query: str) -> QueryAnalysis:
        """Use OpenAI to intelligently analyze the user's query and extract intent"""
        if not self.api_key:
            return self._fallback_query_analysis(user_query)
        
        try:
            prompt = f"""
You are an expert at analyzing user queries about employee performance and task management.

Analyze this user query and determine:
1. Is this asking about a specific employee's performance/tasks?
2. What is the employee's name (if mentioned)?
3. What specific information are they looking for?
4. How confident are you in this analysis?

User Query: "{user_query}"

Respond with a JSON object containing:
{{
    "is_employee_query": true/false,
    "employee_name": "extracted name or null",
    "intent": "what they want to know",
    "confidence": 0.0-1.0,
    "query_type": "performance_report|task_status|productivity_analysis|general",
    "additional_context": {{
        "time_period": "recent|weekly|monthly|all_time|null",
        "specific_metrics": ["completion_rate", "overdue_tasks", "productivity"],
        "comparison_requested": true/false
    }}
}}

Examples:
- "Give me Hamza report about tasks" → employee_name: "Hamza", intent: "performance report", query_type: "performance_report"
- "How is John doing with his projects?" → employee_name: "John", intent: "project performance", query_type: "performance_report"
- "Show me Sarah's overdue tasks" → employee_name: "Sarah", intent: "overdue task analysis", query_type: "task_status"
"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert query analyzer for employee performance systems. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    analysis_data = json.loads(json_text)
                    
                    return QueryAnalysis(
                        is_employee_query=analysis_data.get('is_employee_query', False),
                        employee_name=analysis_data.get('employee_name'),
                        intent=analysis_data.get('intent', 'unknown'),
                        confidence=analysis_data.get('confidence', 0.5),
                        query_type=analysis_data.get('query_type', 'general'),
                        additional_context=analysis_data.get('additional_context', {})
                    )
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse OpenAI response as JSON: {e}")
                print(f"Raw response: {response_text}")
                return self._fallback_query_analysis(user_query)
            
        except Exception as e:
            print(f"OpenAI query analysis failed: {e}")
            return self._fallback_query_analysis(user_query)
    
    def _fallback_query_analysis(self, user_query: str) -> QueryAnalysis:
        """Fallback query analysis using simple pattern matching when OpenAI is not available"""
        query_lower = user_query.lower()
        
        # Employee-related keywords
        employee_keywords = [
            'report', 'performance', 'tasks', 'analyze', 'how is', 'status of', 
            'productivity', 'doing', 'working on', 'progress', 'overdue',
            'completed', 'assigned to', 'responsible for'
        ]
        
        # Check if this looks like an employee query
        is_employee_query = any(keyword in query_lower for keyword in employee_keywords)
        
        # Simple name extraction
        employee_name = None
        if is_employee_query:
            words = user_query.split()
            for i, word in enumerate(words):
                if word.lower() in ['give', 'me', 'report', 'about', 'tasks', 'how', 'is', 'analyze', 'performance', 'of', 'for', 'show', 'tell']:
                    continue
                if word.isalpha() and len(word) > 2 and word[0].isupper():
                    employee_name = word
                    break
        
        # Determine query type
        query_type = 'general'
        if 'report' in query_lower or 'performance' in query_lower:
            query_type = 'performance_report'
        elif 'overdue' in query_lower or 'deadline' in query_lower:
            query_type = 'task_status'
        elif 'productivity' in query_lower or 'analyze' in query_lower:
            query_type = 'productivity_analysis'
        
        return QueryAnalysis(
            is_employee_query=is_employee_query,
            employee_name=employee_name,
            intent=f"Employee performance inquiry" if is_employee_query else "General query",
            confidence=0.7 if employee_name else 0.3,
            query_type=query_type,
            additional_context={}
        )
    
    def get_employee_tasks(self, employee_name: str, cursor) -> Dict[str, Any]:
        """Fetch comprehensive task data for an employee from CRM database"""
        try:
            query = """
            SELECT 
                t.id,
                t.name as title,
                t.description,
                t.status,
                t.priority,
                t.startdate as start_time,
                t.duedate as end_time,
                t.dateadded as created_at,
                t.datefinished as finished_at,
                t.addedfrom as created_by,
                p.name as project_name,
                CONCAT(ta.firstname, ' ', ta.lastname) as assignee,
                CONCAT(tc.firstname, ' ', tc.lastname) as creator
            FROM tbltasks t
            LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
            LEFT JOIN tblstaff ta ON t.addedfrom = ta.staffid
            LEFT JOIN tblstaff tc ON t.addedfrom = tc.staffid
            WHERE 
                LOWER(CONCAT(ta.firstname, ' ', ta.lastname)) LIKE LOWER(%s)
                OR LOWER(CONCAT(tc.firstname, ' ', tc.lastname)) LIKE LOWER(%s)
            ORDER BY t.dateadded DESC
            """
            
            name_pattern = f"%{employee_name}%"
            cursor.execute(query, (name_pattern, name_pattern))
            tasks = cursor.fetchall()
            
            return {
                'success': True,
                'tasks': [dict(task) for task in tasks],
                'total_found': len(tasks)
            }
            
        except Exception as e:
            print(f"Error fetching employee tasks: {e}")
            return {
                'success': False,
                'error': str(e),
                'tasks': [],
                'total_found': 0
            }
    
    def analyze_performance_metrics(self, tasks: List[Dict]) -> EmployeePerformance:
        """Analyze raw task data to extract performance metrics"""
        if not tasks:
            return EmployeePerformance(
                employee_name="Unknown",
                total_tasks=0,
                completed_tasks=0,
                in_progress_tasks=0,
                overdue_tasks=0,
                completion_rate=0.0,
                avg_task_duration=None,
                recent_activity=[],
                performance_trend="No data"
            )
        
        # Extract employee name
        employee_name = None
        for task in tasks:
            if task.get('assignee') and task['assignee'].strip():
                employee_name = task['assignee']
                break
            elif task.get('creator') and task['creator'].strip():
                employee_name = task['creator']
                break
        
        # Status mapping
        status_map = {
            0: 'not_started',
            1: 'todo', 
            2: 'in_progress',
            3: 'review',
            4: 'done',
            5: 'done'
        }
        
        # Analyze metrics
        total_tasks = len(tasks)
        completed_tasks = 0
        in_progress_tasks = 0
        overdue_tasks = 0
        
        current_date = datetime.now().date()
        recent_activity = []
        task_durations = []
        
        for task in tasks:
            status = status_map.get(task.get('status', 1), 'todo')
            
            if status == 'done':
                completed_tasks += 1
                
                if task.get('created_at') and task.get('finished_at'):
                    try:
                        start = datetime.fromisoformat(str(task['created_at']))
                        finish = datetime.fromisoformat(str(task['finished_at']))
                        duration = (finish - start).days
                        if duration > 0:
                            task_durations.append(duration)
                    except:
                        pass
                        
            elif status in ['in_progress', 'review']:
                in_progress_tasks += 1
            
            # Check for overdue
            if task.get('end_time') and status != 'done':
                try:
                    due_date = datetime.fromisoformat(str(task['end_time'])).date()
                    if due_date < current_date:
                        overdue_tasks += 1
                except:
                    pass
            
            # Recent activity (last 30 days)
            if task.get('created_at'):
                try:
                    task_date = datetime.fromisoformat(str(task['created_at'])).date()
                    if (current_date - task_date).days <= 30:
                        recent_activity.append({
                            'title': task.get('title', 'Untitled'),
                            'status': status,
                            'date': str(task_date),
                            'project': task.get('project_name', 'No Project')
                        })
                except:
                    pass
        
        # Calculate metrics
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        avg_duration = sum(task_durations) / len(task_durations) if task_durations else None
        
        # Determine trend
        if completion_rate >= 80:
            trend = "Excellent"
        elif completion_rate >= 60:
            trend = "Good"
        elif completion_rate >= 40:
            trend = "Average"
        else:
            trend = "Needs Improvement"
        
        return EmployeePerformance(
            employee_name=employee_name or "Unknown Employee",
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            overdue_tasks=overdue_tasks,
            completion_rate=round(completion_rate, 1),
            avg_task_duration=round(avg_duration, 1) if avg_duration else None,
            recent_activity=recent_activity[:10],
            performance_trend=trend
        )
    
    def generate_ai_analysis(self, performance: EmployeePerformance, query: str, query_analysis: Optional[QueryAnalysis] = None) -> str:
        """Generate intelligent AI analysis using OpenAI with enhanced context understanding"""
        if not self.api_key:
            return self._generate_fallback_analysis(performance, query_analysis)
        
        try:
            context_info = ""
            if query_analysis:
                context_info = f"""
Query Analysis Context:
- User Intent: {query_analysis.intent}
- Query Type: {query_analysis.query_type}
- Confidence: {query_analysis.confidence:.2f}
- Additional Context: {query_analysis.additional_context}
"""

            if query_analysis and query_analysis.query_type == 'task_status':
                focus_area = "Focus particularly on task status, deadlines, and overdue items."
            elif query_analysis and query_analysis.query_type == 'productivity_analysis':
                focus_area = "Focus on productivity metrics, efficiency, and work patterns."
            elif query_analysis and query_analysis.query_type == 'performance_report':
                focus_area = "Provide a comprehensive performance overview with actionable insights."
            else:
                focus_area = "Provide a balanced analysis covering all performance aspects."

            prompt = f"""
You are an expert HR Analytics AI that provides human-like, insightful analysis of employee performance data.

{context_info}

Employee: {performance.employee_name}
Original Query: "{query}"

Performance Data:
- Total Tasks: {performance.total_tasks}
- Completed Tasks: {performance.completed_tasks} ({performance.completion_rate}%)
- In Progress Tasks: {performance.in_progress_tasks}
- Overdue Tasks: {performance.overdue_tasks}
- Average Task Duration: {performance.avg_task_duration} days (if available)
- Performance Trend: {performance.performance_trend}
- Recent Activities: {len(performance.recent_activity)} tasks in last 30 days

{focus_area}

Provide a conversational, intelligent response that:
1. Directly answers the user's question
2. Gives an honest assessment of how {performance.employee_name} is performing
3. Highlights key metrics in context
4. Identifies strengths and areas for improvement  
5. Offers specific, actionable recommendations
6. Uses natural language like you're talking to a manager

Be insightful, constructive, and human-like. Think like an experienced HR manager who knows how to interpret data and provide valuable insights.
"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert HR analytics assistant that provides intelligent, conversational analysis of employee performance data. Always be helpful, insightful, and constructive."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
            return self._generate_fallback_analysis(performance, query_analysis)
    
    def _generate_fallback_analysis(self, performance: EmployeePerformance, query_analysis: Optional[QueryAnalysis] = None) -> str:
        """Generate enhanced fallback analysis when OpenAI is not available"""
        
        if performance.completion_rate >= 90:
            assessment = f"{performance.employee_name} is performing exceptionally well!"
            performance_level = "exceptional"
        elif performance.completion_rate >= 80:
            assessment = f"{performance.employee_name} is performing excellently!"
            performance_level = "excellent"
        elif performance.completion_rate >= 70:
            assessment = f"{performance.employee_name} is doing well overall."
            performance_level = "good"
        elif performance.completion_rate >= 50:
            assessment = f"{performance.employee_name} has average performance with room for improvement."
            performance_level = "average"
        else:
            assessment = f"{performance.employee_name} needs significant improvement and support."
            performance_level = "needs_improvement"
        
        analysis = f"""
Performance Report for {performance.employee_name}

{assessment}

Key Performance Metrics:
- Total Tasks: {performance.total_tasks}
- Completed: {performance.completed_tasks} ({performance.completion_rate}%)
- In Progress: {performance.in_progress_tasks}
- Overdue: {performance.overdue_tasks}
- Performance Trend: {performance.performance_trend}

Detailed Analysis:
"""
        
        if query_analysis and query_analysis.query_type == 'task_status':
            analysis += f"Task Status Focus:\n"
            if performance.overdue_tasks > 0:
                analysis += f"Has {performance.overdue_tasks} overdue tasks requiring immediate attention.\n"
            if performance.in_progress_tasks > 0:
                analysis += f"Currently working on {performance.in_progress_tasks} tasks.\n"
            analysis += f"Task completion rate of {performance.completion_rate}% {'is excellent' if performance.completion_rate >= 80 else 'could be improved'}.\n\n"
        
        elif query_analysis and query_analysis.query_type == 'productivity_analysis':
            analysis += f"Productivity Analysis:\n"
            if performance.avg_task_duration:
                analysis += f"Average task completion time: {performance.avg_task_duration} days.\n"
            if performance.completion_rate >= 80:
                analysis += f"High productivity with {performance.completion_rate}% completion rate.\n"
            elif performance.completion_rate < 60:
                analysis += f"Productivity could be improved - currently at {performance.completion_rate}% completion.\n"
            analysis += f"Recent activity shows {len(performance.recent_activity)} tasks worked on in the last 30 days.\n\n"
        
        if performance.overdue_tasks > 0:
            urgency = "high" if performance.overdue_tasks > 3 else "moderate"
            analysis += f"Attention Needed: {performance.overdue_tasks} overdue tasks ({urgency} priority).\n"
        
        if performance.completion_rate >= 80:
            analysis += f"Strength: Excellent task completion rate shows strong productivity and time management.\n"
        elif performance.completion_rate < 50:
            analysis += f"Improvement Area: Low completion rate suggests need for better task prioritization or workload adjustment.\n"
        
        if performance.in_progress_tasks > performance.completed_tasks and performance.total_tasks > 5:
            analysis += f"Note: High number of in-progress tasks may indicate multitasking challenges or task complexity issues.\n"
        
        analysis += f"\nRecommendations:\n"
        if performance_level == "exceptional":
            analysis += f"- Consider assigning {performance.employee_name} to mentor other team members\n"
            analysis += f"- Explore opportunities for increased responsibilities or leadership roles\n"
        elif performance_level == "excellent":
            analysis += f"- Maintain current performance standards\n"
            analysis += f"- Consider challenging projects to further develop skills\n"
        elif performance_level == "good":
            analysis += f"- Focus on completing overdue tasks if any\n"
            analysis += f"- Optimize task prioritization strategies\n"
        elif performance_level in ["average", "needs_improvement"]:
            analysis += f"- Schedule one-on-one meetings to identify blockers\n"
            analysis += f"- Consider workload rebalancing or additional support\n"
            analysis += f"- Implement task management tools or training\n"
        
        analysis += f"\nRecent Activity: {len(performance.recent_activity)} tasks worked on in the last 30 days."
        
        return analysis
    
    def get_cached_performance(self, employee_name: str) -> Optional[EmployeePerformance]:
        """Get cached performance data if still valid"""
        cache_key = employee_name.lower().strip()
        
        if cache_key in self.employee_cache:
            if datetime.now().timestamp() < self.cache_expiry.get(cache_key, 0):
                return self.employee_cache[cache_key]
            else:
                del self.employee_cache[cache_key]
                if cache_key in self.cache_expiry:
                    del self.cache_expiry[cache_key]
        
        return None
    
    def cache_performance(self, employee_name: str, performance: EmployeePerformance):
        """Cache performance data"""
        cache_key = employee_name.lower().strip()
        self.employee_cache[cache_key] = performance
        self.cache_expiry[cache_key] = datetime.now().timestamp() + self.cache_duration
    
    def clear_cache(self):
        """Clear the performance cache"""
        self.employee_cache.clear()
        self.cache_expiry.clear()
        print("Performance cache cleared")
    
    def analyze_employee(self, employee_name: str, query: str, cursor) -> Dict[str, Any]:
        """
        Main method to analyze employee performance with intelligent NLP processing
        """
        try:
            print(f"Processing query with AI: '{query}'")
            
            # Step 1: Analyze the query with OpenAI to understand intent
            query_analysis = self.analyze_query_with_ai(query)
            
            print(f"Query Analysis Results:")
            print(f"  - Is Employee Query: {query_analysis.is_employee_query}")
            print(f"  - Detected Employee: {query_analysis.employee_name}")
            print(f"  - Intent: {query_analysis.intent}")
            print(f"  - Confidence: {query_analysis.confidence:.2f}")
            print(f"  - Query Type: {query_analysis.query_type}")
            
            # If this is not an employee query, return appropriate response
            if not query_analysis.is_employee_query or query_analysis.confidence < 0.3:
                return {
                    'success': False,
                    'error': 'This query does not appear to be asking about a specific employee. Please ask about an employee\'s performance, tasks, or productivity.',
                    'suggestions': [
                        'Try: "Give me John\'s performance report"',
                        'Try: "How is Sarah doing with her tasks?"',
                        'Try: "Show me Alex\'s overdue tasks"',
                        'Try: "Analyze Maria\'s productivity this month"'
                    ],
                    'query_analysis': query_analysis.__dict__
                }
            
            # Step 2: Determine the employee name to analyze
            target_employee = query_analysis.employee_name or employee_name
            
            if not target_employee:
                return {
                    'success': False,
                    'error': 'Could not identify which employee you want to analyze. Please specify an employee name.',
                    'query_analysis': query_analysis.__dict__
                }
            
            print(f"Analyzing performance for: {target_employee}")
            
            # Step 3: Check cache first
            cached_performance = self.get_cached_performance(target_employee)
            if cached_performance:
                print("Using cached performance data")
                analysis = self.generate_ai_analysis(cached_performance, query, query_analysis)
                return {
                    'success': True,
                    'employee': target_employee,
                    'analysis': analysis,
                    'performance_data': cached_performance.__dict__,
                    'query_analysis': query_analysis.__dict__,
                    'cached': True
                }
            
            # Step 4: Fetch fresh data from database
            task_data = self.get_employee_tasks(target_employee, cursor)
            
            if not task_data['success']:
                return {
                    'success': False,
                    'error': f"Failed to fetch tasks for {target_employee}: {task_data['error']}",
                    'query_analysis': query_analysis.__dict__
                }
            
            if task_data['total_found'] == 0:
                return {
                    'success': False,
                    'error': f"No tasks found for employee '{target_employee}'. Please check the spelling or try a different name.",
                    'suggestions': [
                        'Check if the name is spelled correctly',
                        'Try using just the first name',
                        'Make sure the employee has tasks assigned in the system'
                    ],
                    'query_analysis': query_analysis.__dict__
                }
            
            # Step 5: Analyze performance metrics
            performance = self.analyze_performance_metrics(task_data['tasks'])
            
            # Step 6: Cache the results
            self.cache_performance(target_employee, performance)
            
            # Step 7: Generate intelligent AI analysis based on query context
            analysis = self.generate_ai_analysis(performance, query, query_analysis)
            
            print(f"Analysis complete for {target_employee}")
            
            return {
                'success': True,
                'employee': target_employee,
                'analysis': analysis,
                'performance_data': performance.__dict__,
                'query_analysis': query_analysis.__dict__,
                'cached': False,
                'total_tasks_found': task_data['total_found']
            }
            
        except Exception as e:
            print(f"Error analyzing employee: {e}")
            return {
                'success': False,
                'error': f"Analysis failed: {str(e)}"
            }