"""
AI Response Generator - OpenAI GPT-4o integration for task management
Handles response generation with retrieval-augmented generation (RAG)
"""

import time
import json
from typing import Dict, List, Optional, Any
import openai
from datetime import datetime, timedelta
from .config import Config
from .logger import get_logger

logger = get_logger()

class TaskResponseGenerator:
    """Generates AI responses using OpenAI GPT-4o with RAG"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_response(self, intent: str, employee: str, retrieved_data: Dict[str, Any], 
                         original_query: str) -> Dict[str, Any]:
        """
        Generate AI response based on intent and retrieved data
        Args:
            intent: User intent (list_tasks, task_summary, etc.)
            employee: Employee name
            retrieved_data: Data from retriever layer
            original_query: Original user query
        Returns: Structured response dictionary
        """
        start_time = time.time()
        
        try:
            # Route to appropriate generator based on intent
            if intent == 'list_tasks':
                response = self._generate_task_list(employee, retrieved_data, original_query)
            elif intent == 'task_summary':
                response = self._generate_task_summary(employee, retrieved_data, original_query)
            elif intent == 'performance_report':
                response = self._generate_performance_report(employee, retrieved_data, original_query)
            elif intent == 'anomaly_check':
                response = self._generate_anomaly_report(employee, retrieved_data, original_query)
            else:
                response = self._generate_generic_response(employee, retrieved_data, original_query)
            
            # Add metadata
            response.update({
                'intent': intent,
                'employee': employee,
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'data_source': retrieved_data.get('retrieval_method', 'unknown')
            })
            
            logger.info(f"Generated {intent} response for {employee}", 
                       extra_data={'response_length': len(str(response))})
            
            return response
            
        except Exception as e:
            logger.error("Failed to generate response", error=e, 
                        extra_data={'intent': intent, 'employee': employee})
            return {
                'error': str(e),
                'intent': intent,
                'employee': employee,
                'processing_time': time.time() - start_time
            }
    
    def _generate_task_list(self, employee: str, retrieved_data: Dict[str, Any], 
                           query: str) -> Dict[str, Any]:
        """Generate task list response - direct MySQL data"""
        tasks = retrieved_data.get('tasks', [])
        
        if not tasks:
            return {
                'response_type': 'task_list',
                'message': f"No active tasks found for {employee}.",
                'tasks': [],
                'total_count': 0
            }
        
        # Format tasks for display
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                'id': task['id'],
                'name': task['name'],
                'status': task['status_name'],
                'priority': task['priority_name'],
                'project': task.get('project_name', 'No Project'),
                'due_date': task.get('duedate'),
                'is_overdue': task.get('is_overdue', False)
            }
            
            if task.get('is_overdue'):
                formatted_task['days_overdue'] = task.get('days_overdue', 0)
            
            formatted_tasks.append(formatted_task)
        
        return {
            'response_type': 'task_list',
            'message': f"Found {len(tasks)} active tasks for {employee}",
            'tasks': formatted_tasks,
            'total_count': retrieved_data.get('total_count', len(tasks))
        }
    
    def _generate_task_summary(self, employee: str, retrieved_data: Dict[str, Any], 
                              query: str) -> Dict[str, Any]:
        """Generate AI-powered task summary"""
        tasks = retrieved_data.get('tasks', [])
        
        if not tasks:
            return {
                'response_type': 'task_summary',
                'ai_summary': f"{employee} currently has no active tasks.",
                'key_insights': [],
                'task_breakdown': {}
            }
        
        # Prepare context for OpenAI
        context = self._prepare_task_context(tasks, employee)
        
        try:
            start_time = time.time()
            
            prompt = self._build_summary_prompt(employee, context, query)
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL_GPT,
                messages=[
                    {"role": "system", "content": "You are a task management AI assistant. Provide concise, actionable insights about employee tasks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.OPENAI_MAX_TOKENS,
                temperature=Config.OPENAI_TEMPERATURE
            )
            
            ai_response = response.choices[0].message.content
            response_time = time.time() - start_time
            
            logger.log_openai_request(
                Config.OPENAI_MODEL_GPT, response.usage.total_tokens,
                response_time, True
            )
            
            # Generate additional insights
            task_breakdown = self._analyze_task_breakdown(tasks)
            key_insights = self._extract_key_insights(tasks)
            
            return {
                'response_type': 'task_summary',
                'ai_summary': ai_response,
                'key_insights': key_insights,
                'task_breakdown': task_breakdown,
                'retrieved_tasks': len(tasks)
            }
            
        except Exception as e:
            logger.log_openai_request(Config.OPENAI_MODEL_GPT, 0, 0, False, str(e))
            
            # Fallback to rule-based summary
            return self._generate_fallback_summary(employee, tasks)
    
    def _generate_performance_report(self, employee: str, retrieved_data: Dict[str, Any], 
                                   query: str) -> Dict[str, Any]:
        """Generate performance analysis report"""
        tasks = retrieved_data.get('tasks', [])
        
        if not tasks:
            return {
                'response_type': 'performance_report',
                'message': f"No task data available for {employee} performance analysis.",
                'metrics': {}
            }
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(tasks)
        
        # Generate AI analysis
        try:
            ai_analysis = self._generate_performance_analysis(employee, tasks, metrics)
        except Exception as e:
            logger.error("Failed to generate AI performance analysis", error=e)
            ai_analysis = "Performance analysis temporarily unavailable."
        
        return {
            'response_type': 'performance_report',
            'ai_analysis': ai_analysis,
            'metrics': metrics,
            'recommendations': self._generate_performance_recommendations(metrics),
            'total_tasks_analyzed': len(tasks)
        }
    
    def _generate_anomaly_report(self, employee: str, retrieved_data: Dict[str, Any], 
                               query: str) -> Dict[str, Any]:
        """Generate anomaly detection report"""
        tasks = retrieved_data.get('tasks', [])
        
        if not tasks:
            return {
                'response_type': 'anomaly_report',
                'message': f"No active tasks to analyze for {employee}.",
                'anomalies': []
            }
        
        # Detect anomalies
        anomalies = self._detect_task_anomalies(tasks)
        
        # Generate AI analysis if anomalies found
        ai_analysis = ""
        if anomalies:
            try:
                ai_analysis = self._generate_anomaly_analysis(employee, anomalies, tasks)
            except Exception as e:
                logger.error("Failed to generate AI anomaly analysis", error=e)
                ai_analysis = "Anomaly analysis temporarily unavailable."
        
        return {
            'response_type': 'anomaly_report',
            'ai_analysis': ai_analysis,
            'anomalies': anomalies,
            'total_issues_found': len(anomalies),
            'severity_breakdown': self._categorize_anomalies(anomalies)
        }
    
    def _generate_generic_response(self, employee: str, retrieved_data: Dict[str, Any], 
                                 query: str) -> Dict[str, Any]:
        """Generate generic response for unknown intents"""
        return {
            'response_type': 'generic',
            'message': f"I can help you with task information for {employee}. Try asking about task lists, summaries, performance reports, or checking for issues.",
            'available_commands': [
                "Show me tasks for [employee]",
                "Summarize [employee]'s work",
                "Generate performance report for [employee]",
                "Check for issues in [employee]'s tasks"
            ]
        }
    
    def _prepare_task_context(self, tasks: List[Dict[str, Any]], employee: str) -> str:
        """Prepare task context for OpenAI prompt"""
        context_parts = [f"Employee: {employee}", f"Total Active Tasks: {len(tasks)}", ""]
        
        for i, task in enumerate(tasks[:10], 1):  # Limit to top 10 tasks
            task_info = [
                f"Task {i}: {task['name']}",
                f"  Status: {task.get('status_name', 'Unknown')}",
                f"  Priority: {task.get('priority_name', 'Unknown')}",
                f"  Project: {task.get('project_name', 'No Project')}"
            ]
            
            if task.get('duedate'):
                task_info.append(f"  Due Date: {task['duedate']}")
            
            if task.get('is_overdue'):
                task_info.append(f"  ⚠️ OVERDUE by {task.get('days_overdue', 0)} days")
            
            context_parts.append("\n".join(task_info))
            context_parts.append("")
        
        if len(tasks) > 10:
            context_parts.append(f"... and {len(tasks) - 10} more tasks")
        
        return "\n".join(context_parts)
    
    def _build_summary_prompt(self, employee: str, context: str, query: str) -> str:
        """Build prompt for task summary generation"""
        return f"""
Analyze the following task data for {employee} and provide a concise summary:

{context}

Original Query: "{query}"

Please provide:
1. A brief overview of {employee}'s current workload
2. Key focus areas and priorities
3. Any notable patterns or concerns
4. Actionable insights or recommendations

Keep the response professional, concise, and actionable (max 200 words).
"""
    
    def _analyze_task_breakdown(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze task breakdown by various dimensions"""
        breakdown = {
            'by_status': {},
            'by_priority': {},
            'by_project': {},
            'overdue_count': 0
        }
        
        for task in tasks:
            # By status
            status = task.get('status_name', 'Unknown')
            breakdown['by_status'][status] = breakdown['by_status'].get(status, 0) + 1
            
            # By priority
            priority = task.get('priority_name', 'Unknown')
            breakdown['by_priority'][priority] = breakdown['by_priority'].get(priority, 0) + 1
            
            # By project
            project = task.get('project_name') or 'No Project'
            breakdown['by_project'][project] = breakdown['by_project'].get(project, 0) + 1
            
            # Overdue count
            if task.get('is_overdue'):
                breakdown['overdue_count'] += 1
        
        return breakdown
    
    def _extract_key_insights(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from task data"""
        insights = []
        
        # Check for high priority tasks
        urgent_tasks = [t for t in tasks if t.get('priority') == 4]
        if urgent_tasks:
            insights.append(f"🚨 {len(urgent_tasks)} urgent tasks require immediate attention")
        
        # Check for overdue tasks
        overdue_tasks = [t for t in tasks if t.get('is_overdue')]
        if overdue_tasks:
            insights.append(f"⏰ {len(overdue_tasks)} tasks are overdue")
        
        # Check for project concentration
        projects = {}
        for task in tasks:
            project = task.get('project_name') or 'No Project'
            projects[project] = projects.get(project, 0) + 1
        
        if projects:
            main_project = max(projects, key=projects.get)
            if projects[main_project] >= len(tasks) * 0.6:
                insights.append(f"🎯 Primarily focused on {main_project} ({projects[main_project]} tasks)")
        
        # Check for task status distribution
        in_progress = [t for t in tasks if t.get('status') == 2]
        if len(in_progress) >= len(tasks) * 0.7:
            insights.append("🔄 Most tasks are currently in progress")
        
        return insights
    
    def _calculate_performance_metrics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics from task data"""
        total_tasks = len(tasks)
        completed_tasks = [t for t in tasks if t.get('status') == 5]
        overdue_tasks = [t for t in tasks if t.get('is_overdue')]
        urgent_tasks = [t for t in tasks if t.get('priority') == 4]
        
        metrics = {
            'total_tasks': total_tasks,
            'completed_tasks': len(completed_tasks),
            'active_tasks': total_tasks - len(completed_tasks),
            'overdue_tasks': len(overdue_tasks),
            'urgent_tasks': len(urgent_tasks),
            'completion_rate': (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0,
            'overdue_rate': (len(overdue_tasks) / total_tasks * 100) if total_tasks > 0 else 0
        }
        
        # Calculate average days overdue
        if overdue_tasks:
            total_days_overdue = sum(t.get('days_overdue', 0) for t in overdue_tasks)
            metrics['avg_days_overdue'] = total_days_overdue / len(overdue_tasks)
        else:
            metrics['avg_days_overdue'] = 0
        
        return metrics
    
    def _generate_performance_analysis(self, employee: str, tasks: List[Dict[str, Any]], 
                                     metrics: Dict[str, Any]) -> str:
        """Generate AI-powered performance analysis"""
        start_time = time.time()
        
        context = f"""
Employee: {employee}
Performance Metrics:
- Total Tasks: {metrics['total_tasks']}
- Completed: {metrics['completed_tasks']} ({metrics['completion_rate']:.1f}%)
- Active: {metrics['active_tasks']}
- Overdue: {metrics['overdue_tasks']} ({metrics['overdue_rate']:.1f}%)
- Urgent: {metrics['urgent_tasks']}
- Average Days Overdue: {metrics['avg_days_overdue']:.1f}

Recent Task Sample:
{self._prepare_task_context(tasks[:5], employee)}
"""
        
        prompt = f"""
Analyze the performance data for {employee} and provide insights:

{context}

Provide a professional performance analysis including:
1. Overall performance assessment
2. Strengths and areas for improvement
3. Specific recommendations
4. Comparison to typical performance benchmarks

Keep response under 300 words and focus on actionable insights.
"""
        
        response = self.openai_client.chat.completions.create(
            model=Config.OPENAI_MODEL_GPT,
            messages=[
                {"role": "system", "content": "You are a performance analysis expert providing objective, constructive feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=Config.OPENAI_MAX_TOKENS,
            temperature=Config.OPENAI_TEMPERATURE
        )
        
        response_time = time.time() - start_time
        logger.log_openai_request(
            Config.OPENAI_MODEL_GPT, response.usage.total_tokens,
            response_time, True
        )
        
        return response.choices[0].message.content
    
    def _generate_performance_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        if metrics['overdue_rate'] > Config.PERFORMANCE_THRESHOLDS['overdue_threshold_critical']:
            recommendations.append("🚨 Critical: Address overdue tasks immediately to prevent project delays")
        elif metrics['overdue_rate'] > Config.PERFORMANCE_THRESHOLDS['overdue_threshold_warning']:
            recommendations.append("⚠️ Focus on completing overdue tasks to improve delivery performance")
        
        if metrics['completion_rate'] < Config.PERFORMANCE_THRESHOLDS['completion_rate_poor']:
            recommendations.append("📈 Consider workload rebalancing or additional support to improve completion rate")
        elif metrics['completion_rate'] > Config.PERFORMANCE_THRESHOLDS['completion_rate_excellent']:
            recommendations.append("🎉 Excellent completion rate! Consider taking on additional responsibilities")
        
        if metrics['urgent_tasks'] > 5:
            recommendations.append("🎯 High number of urgent tasks - review prioritization and time management")
        
        return recommendations
    
    def _detect_task_anomalies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in task data"""
        anomalies = []
        
        for task in tasks:
            # Long overdue tasks
            if task.get('is_overdue') and task.get('days_overdue', 0) > 14:
                anomalies.append({
                    'type': 'long_overdue',
                    'severity': 'high',
                    'task_id': task['id'],
                    'task_name': task['name'],
                    'description': f"Task overdue by {task['days_overdue']} days",
                    'days_overdue': task['days_overdue']
                })
            
            # Tasks stuck in testing
            if task.get('status') == 3:  # Testing status
                anomalies.append({
                    'type': 'stuck_in_testing',
                    'severity': 'medium',
                    'task_id': task['id'],
                    'task_name': task['name'],
                    'description': "Task has been in testing status - may need review"
                })
            
            # Urgent tasks not in progress
            if task.get('priority') == 4 and task.get('status') == 1:  # Urgent but not started
                anomalies.append({
                    'type': 'urgent_not_started',
                    'severity': 'high',
                    'task_id': task['id'],
                    'task_name': task['name'],
                    'description': "Urgent task has not been started"
                })
        
        return anomalies
    
    def _generate_anomaly_analysis(self, employee: str, anomalies: List[Dict[str, Any]], 
                                 tasks: List[Dict[str, Any]]) -> str:
        """Generate AI analysis of detected anomalies"""
        start_time = time.time()
        
        anomaly_summary = "\n".join([
            f"- {anomaly['type']}: {anomaly['description']}"
            for anomaly in anomalies[:10]  # Limit to top 10
        ])
        
        prompt = f"""
Analyze the following task anomalies for {employee}:

{anomaly_summary}

Total anomalies detected: {len(anomalies)}

Provide a brief analysis including:
1. Root cause assessment
2. Impact on productivity
3. Specific action items
4. Prevention strategies

Keep response under 200 words and focus on actionable solutions.
"""
        
        response = self.openai_client.chat.completions.create(
            model=Config.OPENAI_MODEL_GPT,
            messages=[
                {"role": "system", "content": "You are a task management expert specializing in identifying and solving workflow issues."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=Config.OPENAI_MAX_TOKENS,
            temperature=Config.OPENAI_TEMPERATURE
        )
        
        response_time = time.time() - start_time
        logger.log_openai_request(
            Config.OPENAI_MODEL_GPT, response.usage.total_tokens,
            response_time, True
        )
        
        return response.choices[0].message.content
    
    def _categorize_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize anomalies by severity"""
        categories = {'high': 0, 'medium': 0, 'low': 0}
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            categories[severity] = categories.get(severity, 0) + 1
        
        return categories
    
    def _generate_fallback_summary(self, employee: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback summary when OpenAI is unavailable"""
        task_breakdown = self._analyze_task_breakdown(tasks)
        key_insights = self._extract_key_insights(tasks)
        
        # Create simple summary
        summary_parts = [
            f"{employee} has {len(tasks)} active tasks.",
        ]
        
        if task_breakdown['overdue_count'] > 0:
            summary_parts.append(f"{task_breakdown['overdue_count']} tasks are overdue.")
        
        if task_breakdown['by_priority'].get('Urgent', 0) > 0:
            summary_parts.append(f"{task_breakdown['by_priority']['Urgent']} urgent tasks need attention.")
        
        return {
            'response_type': 'task_summary',
            'ai_summary': ' '.join(summary_parts),
            'key_insights': key_insights,
            'task_breakdown': task_breakdown,
            'retrieved_tasks': len(tasks),
            'fallback_mode': True
        }

# Global generator instance
response_generator = TaskResponseGenerator()

def get_response_generator() -> TaskResponseGenerator:
    """Get the global response generator instance"""
    return response_generator